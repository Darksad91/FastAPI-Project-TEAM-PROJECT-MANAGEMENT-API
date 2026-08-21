from base64 import urlsafe_b64decode, urlsafe_b64encode
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.users import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
USER_ROLE = "USER"
ADMIN_ROLE = "ADMIN"


class InvalidTokenError(ValueError):
    """JWT khong dung dinh dang, thuat toan hoac chu ky."""


class ExpiredTokenError(ValueError):
    """JWT da qua thoi diem het han."""


def hash_password(password: str) -> str:
    """Hash mat khau bang bcrypt truoc khi luu vao database."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Kiem tra mat khau dau vao co trung voi bcrypt hash da luu hay khong."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Tao access token JWT cho nguoi dung da xac thuc."""
    if settings.ALGORITHM != "HS256":
        raise ValueError("Chi ho tro thuat toan JWT HS256")

    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    header = {"alg": settings.ALGORITHM, "typ": "JWT"}
    payload = {"sub": subject, "exp": int(expires_at.timestamp())}

    def encode_segment(value: dict[str, str | int]) -> str:
        raw_value = json.dumps(value, separators=(",", ":")).encode("utf-8")
        return urlsafe_b64encode(raw_value).rstrip(b"=").decode("ascii")

    signing_input = f"{encode_segment(header)}.{encode_segment(payload)}"
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')}"


def decode_access_token(token: str) -> dict[str, str | int]:
    """Xac thuc va giai ma JWT HS256, bao gom kiem tra thoi han token."""
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}"
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied_signature = urlsafe_b64decode(
            signature_segment + "=" * (-len(signature_segment) % 4)
        )
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise InvalidTokenError("Chu ky JWT khong hop le")

        header = json.loads(
            urlsafe_b64decode(header_segment + "=" * (-len(header_segment) % 4))
        )
        payload = json.loads(
            urlsafe_b64decode(payload_segment + "=" * (-len(payload_segment) % 4))
        )
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise InvalidTokenError("JWT khong dung thuat toan")
        if not isinstance(payload.get("sub"), str):
            raise InvalidTokenError("JWT thieu subject")
        expires_at = payload.get("exp")
        if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
            raise InvalidTokenError("JWT thieu thoi han")
        if expires_at <= datetime.now(timezone.utc).timestamp():
            raise ExpiredTokenError("JWT da het han")
        return payload
    except ExpiredTokenError:
        raise
    except (
        AttributeError,
        binascii.Error,
        UnicodeDecodeError,
        UnicodeEncodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise InvalidTokenError("JWT khong hop le") from exc


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Lay nguoi dung hien tai tu Bearer JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Khong the xac thuc token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token da het han",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tai khoan da bi vo hieu hoa",
        )
    return user


def require_role(*allowed_roles: str):
    """Tao dependency chi cho phep nguoi dung thuoc cac role duoc chi dinh."""
    normalized_roles = {role.upper() for role in allowed_roles}
    if not normalized_roles or not normalized_roles.issubset({USER_ROLE, ADMIN_ROLE}):
        raise ValueError("Role hop le la USER hoac ADMIN")

    def role_guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.upper() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ban khong co quyen truy cap tai nguyen nay",
            )
        return current_user

    return role_guard


require_admin = require_role(ADMIN_ROLE)

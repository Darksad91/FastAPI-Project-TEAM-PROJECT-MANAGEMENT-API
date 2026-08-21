from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json

import bcrypt

from app.core.config import settings


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

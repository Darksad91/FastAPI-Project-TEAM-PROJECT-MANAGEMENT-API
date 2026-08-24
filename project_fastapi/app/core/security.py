import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db

# HTTPBearer tự động đọc "Authorization: Bearer <token>" từ header
bearer_scheme = HTTPBearer()


# ------------------------------------------------------------------ #
#  Mật khẩu                                                           #
# ------------------------------------------------------------------ #

def hash_password(password: str) -> str:
    """Băm mật khẩu trước khi lưu vào DB."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập có khớp với mật khẩu đã băm không."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ------------------------------------------------------------------ #
#  JWT Token                                                           #
# ------------------------------------------------------------------ #

def create_access_token(subject: str) -> str:
    """
    Tạo JWT access token.
    - subject: thường là user_id dạng string (ví dụ: "42")
    - Token sẽ hết hạn sau ACCESS_TOKEN_EXPIRE_MINUTES phút (đọc từ .env)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,   # subject — lưu user_id
        "exp": expire,    # expiration — thời điểm hết hạn
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


# ------------------------------------------------------------------ #
#  Dependencies — dùng với Depends() trong router                      #
# ------------------------------------------------------------------ #

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Dependency bảo vệ route: giải mã JWT và trả về user đang đăng nhập.

    Cách dùng trong router:
        current_user: User = Depends(get_current_user)
    """
    from app.models.users import User  # import ở đây để tránh circular import

    # Lỗi trả về nếu token không hợp lệ
    invalid_token_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Bước 1: Giải mã token
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.PyJWTError:
        raise invalid_token_error

    # Bước 2: Lấy user_id từ payload
    user_id = payload.get("sub")
    if user_id is None:
        raise invalid_token_error

    # Bước 3: Tìm user trong DB
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise invalid_token_error

    return user


def require_admin(current_user=Depends(get_current_user)):
    """
    Dependency kiểm tra quyền ADMIN.
    Dùng cho các route chỉ dành cho admin.

    Cách dùng trong router:
        _: User = Depends(require_admin)
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ADMIN mới có quyền truy cập chức năng này",
        )
    return current_user
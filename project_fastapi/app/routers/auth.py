from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.database import get_db
from app.models.users import User
from app.schemas.users import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới. Trả về thông tin user vừa tạo (không có password)."""

    # Bước 1: Kiểm tra email đã tồn tại trong DB chưa
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được sử dụng, vui lòng dùng email khác",
        )

    # Bước 2: Tạo user mới — băm password trước khi lưu
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Reload để lấy id, created_at do DB tự tạo

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Đăng nhập bằng email và password. Trả về JWT access token nếu thành công."""

    # Bước 1: Tìm user theo email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Bước 2: Kiểm tra user tồn tại và password đúng
    # Lưu ý: gộp 2 điều kiện vào 1 thông báo lỗi để không lộ thông tin
    # (tránh kẻ xấu biết email nào đã đăng ký)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Bước 3: Kiểm tra tài khoản có bị khóa không
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa, vui lòng liên hệ quản trị viên",
        )

    # Bước 4: Tạo và trả về JWT token
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Trả về thông tin của người dùng đang đăng nhập (đọc từ Bearer token)."""
    return current_user

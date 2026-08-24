from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.database import get_db
from app.models.users import User
from app.schemas.users import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Trả về hồ sơ của người dùng đang đăng nhập."""
    return current_user


@router.get("", response_model=list[UserResponse])
def list_users(
    search: str | None = Query(default=None, max_length=255),
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),  # Chỉ ADMIN mới được gọi route này
):
    """Danh sách tất cả user — chỉ dành cho ADMIN. Có thể lọc theo tên/email và trạng thái."""

    # Lấy tất cả user
    query = db.query(User)

    # Lọc theo từ khóa tìm kiếm (nếu có)
    if search:
        search = search.strip()
        keyword = f"%{search}%"
        query = query.filter(
            User.full_name.ilike(keyword) | User.email.ilike(keyword)
        )

    # Lọc theo trạng thái (nếu có)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.order_by(User.id).all()

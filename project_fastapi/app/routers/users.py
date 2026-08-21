from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.database import get_db
from app.models.users import User
from app.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Tra ve ho so cua nguoi dung hien tai."""
    return current_user


@router.get("", response_model=list[UserResponse])
def list_users(
    search: str | None = Query(default=None, max_length=255),
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Danh sach user cho ADMIN, co the loc theo ten/email va trang thai."""
    query = db.query(User)

    if search and (search := search.strip()):
        keyword = f"%{search}%"
        query = query.filter(
            or_(User.full_name.ilike(keyword), User.email.ilike(keyword))
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.order_by(User.id).all()

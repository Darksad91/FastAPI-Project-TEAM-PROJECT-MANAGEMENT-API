from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.users import User
from app.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Tra ve ho so cua nguoi dung hien tai."""
    return current_user

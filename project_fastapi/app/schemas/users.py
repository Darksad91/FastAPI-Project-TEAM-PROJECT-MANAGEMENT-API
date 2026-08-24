import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import UserRole


# ------------------------------------------------------------------ #
#  Schema để nhận dữ liệu từ client (Request)                          #
# ------------------------------------------------------------------ #

class UserCreate(BaseModel):
    """Dữ liệu cần thiết để đăng ký tài khoản mới."""
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Chuẩn hóa email: xóa khoảng trắng, chuyển về chữ thường, kiểm tra định dạng."""
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Email không hợp lệ")
        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        """Xóa khoảng trắng đầu/cuối và kiểm tra không được để trống."""
        value = value.strip()
        if not value:
            raise ValueError("Họ tên không được để trống")
        return value


class UserLogin(BaseModel):
    """Dữ liệu cần thiết để đăng nhập."""
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Chuẩn hóa email trước khi tìm trong DB."""
        return value.strip().lower()


class UserUpdate(BaseModel):
    """Dữ liệu để cập nhật thông tin user (tất cả đều optional)."""
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


# ------------------------------------------------------------------ #
#  Schema để trả dữ liệu về cho client (Response)                      #
# ------------------------------------------------------------------ #

class UserResponse(BaseModel):
    """Thông tin user trả về — không bao gồm password."""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Cho phép đọc từ SQLAlchemy object


class TokenResponse(BaseModel):
    """Token trả về sau khi đăng nhập thành công."""
    access_token: str
    token_type: str = "bearer"

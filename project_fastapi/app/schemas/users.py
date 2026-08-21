from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    email: str
    full_name: str


class UserCreate(UserBase):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Email khong hop le")
        return email

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        full_name = value.strip()
        if not full_name:
            raise ValueError("Ho ten khong duoc de trong")
        return full_name


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

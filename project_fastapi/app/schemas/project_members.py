from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectMemberBase(BaseModel):
    role: str


class ProjectMemberCreate(ProjectMemberBase):
    project_id: int
    user_id: int


class ProjectMemberUpdate(BaseModel):
    role: str | None = None


class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    user_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

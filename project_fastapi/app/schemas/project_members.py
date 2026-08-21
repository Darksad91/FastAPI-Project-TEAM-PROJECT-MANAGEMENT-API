from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import ProjectMemberRole


class ProjectMemberBase(BaseModel):
    role: ProjectMemberRole


class ProjectMemberCreate(ProjectMemberBase):
    project_id: int
    user_id: int


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole | None = None


class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    user_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

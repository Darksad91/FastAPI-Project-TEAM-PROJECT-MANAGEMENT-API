from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import ProjectMemberRole


class ProjectMemberBase(BaseModel):
    role: ProjectMemberRole


class ProjectMemberCreate(ProjectMemberBase):
    """Dùng khi tạo trực tiếp qua code (project_id + user_id đều cần truyền)."""
    project_id: int
    user_id: int


class ProjectMemberAdd(BaseModel):
    """
    Dùng cho endpoint POST /projects/{id}/members.
    project_id lấy từ path param nên không cần truyền trong body.
    """
    user_id: int
    role: ProjectMemberRole = ProjectMemberRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole | None = None


class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    user_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

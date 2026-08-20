from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    project_id: int
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class TaskResponse(TaskBase):
    id: int
    project_id: int
    assignee_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    """Schema trả về một bản ghi lịch sử thao tác."""
    id: int
    project_id: int
    actor_id: int
    action: str
    detail: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

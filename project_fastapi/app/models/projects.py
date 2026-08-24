from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Project(Base):
    """
    Bảng dự án.

    Soft delete: khi xóa dự án, không xóa dữ liệu khỏi DB mà chỉ
    bật cờ is_deleted = True và ghi lại thời điểm xóa vào deleted_at.
    Mọi query cần lọc thêm: Project.is_deleted == False.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # --- Soft delete ---
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)   # NULL = chưa xóa

    # --- Quan hệ ---
    owner = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    activity_logs = relationship("ActivityLog", back_populates="project")
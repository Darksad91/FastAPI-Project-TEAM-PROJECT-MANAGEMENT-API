from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), nullable=False, default="TODO")
    priority = Column(String(20), nullable=False, default="MEDIUM")
    due_date = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
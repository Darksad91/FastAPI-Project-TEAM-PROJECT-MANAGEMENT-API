from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )

    role = Column(String(20), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_members")
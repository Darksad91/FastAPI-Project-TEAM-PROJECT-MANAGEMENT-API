from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class ActivityLog(Base):
    """
    Bảng lưu lịch sử các thao tác quan trọng trên dự án.

    Mỗi hành động tạo/sửa/xóa project hoặc thêm/xóa member
    sẽ tạo ra một dòng trong bảng này để tra cứu sau.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Dự án liên quan đến hành động
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Người đã thực hiện hành động
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Loại hành động (giá trị từ ActivityAction enum, ví dụ: "MEMBER_ADDED")
    action = Column(String(50), nullable=False)

    # Mô tả chi tiết thêm (tuỳ chọn), ví dụ: "Thêm user id=5 với role MEMBER"
    detail = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Quan hệ để truy vấn ngược: log.project, log.actor
    project = relationship("Project", back_populates="activity_logs")
    actor = relationship("User")

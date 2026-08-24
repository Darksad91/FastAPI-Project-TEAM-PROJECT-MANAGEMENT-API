"""
Service layer cho Project.

Module này chứa các hàm helper dùng chung cho cả hai router:
  - app/routers/projects.py
  - app/routers/project_members.py

Mục đích:
  - Tránh lặp code giữa các router
  - Tập trung logic kiểm tra quyền và ghi log vào một chỗ dễ bảo trì
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import ActivityAction, ProjectMemberRole
from app.models.activity_logs import ActivityLog
from app.models.project_members import ProjectMember
from app.models.projects import Project


def get_active_project_or_404(project_id: int, db: Session) -> Project:
    """
    Lấy project theo id. Raise HTTP 404 nếu:
      - Không tìm thấy project với id đó
      - Project đã bị xóa mềm (is_deleted = True)
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.is_deleted == False,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với id={project_id}",
        )
    return project


def get_membership_or_403(project_id: int, user_id: int, db: Session) -> ProjectMember:
    """
    Kiểm tra user có là thành viên của project không.
    Raise HTTP 403 nếu user không thuộc dự án.
    Trả về bản ghi ProjectMember nếu hợp lệ (có thể dùng để đọc role).
    """
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải thành viên của dự án này",
        )
    return member


def require_owner_or_403(project_id: int, user_id: int, db: Session) -> None:
    """
    Kiểm tra user có role OWNER trong project không.
    Raise HTTP 403 nếu không phải OWNER.

    Dùng khi muốn giới hạn hành động chỉ cho OWNER:
        require_owner_or_403(project_id, current_user.id, db)
    """
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.role == ProjectMemberRole.OWNER,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER của dự án mới được thực hiện thao tác này",
        )


def log_activity(
    project_id: int,
    actor_id: int,
    action: ActivityAction,
    db: Session,
    detail: str | None = None,
) -> None:
    """
    Ghi một dòng lịch sử thao tác vào bảng activity_logs.

    Lưu ý: hàm này KHÔNG tự commit — người gọi phải tự commit
    cùng với thao tác chính để đảm bảo tính nhất quán (atomicity).

    Ví dụ:
        log_activity(project.id, current_user.id, ActivityAction.PROJECT_CREATED, db,
                     detail="Tạo dự án 'Website mới'")
        db.commit()  # commit cả project lẫn log cùng lúc
    """
    log = ActivityLog(
        project_id=project_id,
        actor_id=actor_id,
        action=action.value,
        detail=detail,
    )
    db.add(log)

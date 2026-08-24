from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import ActivityAction, ProjectMemberRole
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.project_members import ProjectMember
from app.models.users import User
from app.schemas.project_members import ProjectMemberAdd, ProjectMemberResponse
from app.services.project_service import (
    get_active_project_or_404,
    get_membership_or_403,
    log_activity,
    require_owner_or_403,
)

router = APIRouter(prefix="/projects", tags=["Project Members"])


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/members — Danh sách thành viên
# ---------------------------------------------------------------------------

@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xem danh sách thành viên và role của từng người trong dự án.
    Chỉ thành viên của dự án mới được xem.
    """
    # Kiểm tra project tồn tại, chưa bị xóa
    get_active_project_or_404(project_id, db)

    # Kiểm tra current_user là thành viên
    get_membership_or_403(project_id, current_user.id, db)

    # Lấy toàn bộ thành viên của dự án
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
    ).all()

    return members


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/members — Thêm thành viên
# ---------------------------------------------------------------------------

@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Thêm một user vào dự án với role chỉ định. Chỉ OWNER mới được thực hiện.

    Body: { "user_id": 5, "role": "MEMBER" }
    Role mặc định là MEMBER nếu không truyền.
    """
    # Kiểm tra project tồn tại, chưa bị xóa
    get_active_project_or_404(project_id, db)

    # Kiểm tra current_user là OWNER (chỉ OWNER được thêm thành viên)
    require_owner_or_403(project_id, current_user.id, db)

    # Kiểm tra user cần thêm có tồn tại trong hệ thống không
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với id={data.user_id}",
        )

    # Kiểm tra user này đã là thành viên của dự án chưa
    already_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == data.user_id,
    ).first()
    if already_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Người dùng id={data.user_id} đã là thành viên của dự án này",
        )

    # Thêm thành viên mới
    new_member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role=data.role.value,
    )
    db.add(new_member)

    log_activity(
        project_id=project_id,
        actor_id=current_user.id,
        action=ActivityAction.MEMBER_ADDED,
        detail=f"Thêm user id={data.user_id} với role {data.role.value}",
        db=db,
    )

    db.commit()
    db.refresh(new_member)
    return new_member


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}/members/{user_id} — Xóa thành viên
# ---------------------------------------------------------------------------

@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xóa một thành viên khỏi dự án. Chỉ OWNER mới được thực hiện.

    Quy tắc bảo vệ:
      - Nếu user cần xóa là OWNER và là OWNER duy nhất → từ chối (400)
        (để tránh dự án không có ai quản lý)
      - Trả 204 No Content nếu xóa thành công
    """
    # Kiểm tra project tồn tại, chưa bị xóa
    get_active_project_or_404(project_id, db)

    # Kiểm tra current_user là OWNER
    require_owner_or_403(project_id, current_user.id, db)

    # Tìm member cần xóa
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Người dùng id={user_id} không phải thành viên của dự án này",
        )

    # Nếu người cần xóa là OWNER — kiểm tra còn OWNER nào khác không
    if member.role == ProjectMemberRole.OWNER:
        owner_count = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == ProjectMemberRole.OWNER,
        ).count()

        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Không thể xóa OWNER duy nhất của dự án. "
                    "Hãy chuyển quyền OWNER cho người khác trước khi xóa."
                ),
            )

    # Ghi log trước khi xóa (để còn biết role của member vừa bị xóa)
    log_activity(
        project_id=project_id,
        actor_id=current_user.id,
        action=ActivityAction.MEMBER_REMOVED,
        detail=f"Xóa user id={user_id} (role: {member.role}) khỏi dự án",
        db=db,
    )

    db.delete(member)
    db.commit()
    # HTTP 204 No Content — không trả về body

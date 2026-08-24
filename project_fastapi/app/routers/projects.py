from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import ActivityAction, ProjectMemberRole
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.project_members import ProjectMember
from app.models.projects import Project
from app.models.users import User
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import (
    get_active_project_or_404,
    get_membership_or_403,
    log_activity,
    require_owner_or_403,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ---------------------------------------------------------------------------
# POST /projects — Tạo dự án mới
# ---------------------------------------------------------------------------

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tạo dự án mới. Người tạo tự động trở thành OWNER của dự án.

    Quy trình:
      1. Tạo bản ghi Project trong DB
      2. db.flush() để lấy project.id mà chưa commit (vẫn trong cùng transaction)
      3. Thêm người tạo vào project_members với role = OWNER
      4. Ghi activity log
      5. db.commit() — lưu tất cả cùng một lúc (nếu bước nào lỗi, cả 3 đều bị rollback)
    """
    # Bước 1: Tạo project với owner là người đang đăng nhập
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
    )
    db.add(project)

    # Bước 2: flush để DB cấp phát project.id, nhưng chưa kết thúc transaction
    # (cần project.id để tạo ProjectMember ở bước tiếp theo)
    db.flush()

    # Bước 3: Thêm người tạo vào danh sách thành viên với quyền OWNER
    owner_membership = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=ProjectMemberRole.OWNER.value,
    )
    db.add(owner_membership)

    # Bước 4: Ghi lịch sử — ai đã tạo dự án này
    log_activity(
        project_id=project.id,
        actor_id=current_user.id,
        action=ActivityAction.PROJECT_CREATED,
        detail=f"Tạo dự án '{project.name}'",
        db=db,
    )

    # Bước 5: Commit toàn bộ — project, membership và log được lưu cùng lúc
    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# GET /projects — Danh sách dự án của current_user
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ProjectResponse])
def list_my_projects(
    search: str | None = Query(default=None, max_length=255, description="Tìm theo tên dự án"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trả về tất cả dự án mà current_user đang tham gia (dù là OWNER hay MEMBER).
    Hỗ trợ tìm kiếm theo tên (không phân biệt hoa thường).
    """
    # Lấy danh sách project_id mà current_user là thành viên
    # (dùng subquery để tránh load toàn bộ dữ liệu vào bộ nhớ)
    my_project_ids = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.user_id == current_user.id)
        .subquery()
    )

    # Query các project chưa bị xóa và user là thành viên
    query = db.query(Project).filter(
        Project.is_deleted == False,
        Project.id.in_(my_project_ids),
    )

    # Lọc thêm theo tên nếu có từ khóa
    if search and (search := search.strip()):
        query = query.filter(Project.name.ilike(f"%{search}%"))

    # Sắp xếp mới nhất lên đầu
    return query.order_by(Project.created_at.desc()).all()


# ---------------------------------------------------------------------------
# GET /projects/{project_id} — Chi tiết một dự án
# ---------------------------------------------------------------------------

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xem chi tiết một dự án.
    Chỉ thành viên của dự án mới được xem — người ngoài nhận 403.
    """
    # Kiểm tra project tồn tại và chưa bị xóa
    project = get_active_project_or_404(project_id, db)

    # Kiểm tra current_user có là thành viên không
    get_membership_or_403(project_id, current_user.id, db)

    return project


# ---------------------------------------------------------------------------
# PATCH /projects/{project_id} — Cập nhật một phần
# ---------------------------------------------------------------------------

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cập nhật thông tin dự án. Chỉ OWNER mới được thực hiện.

    PATCH — chỉ cập nhật những trường được gửi lên:
      - Gửi {"name": "Tên mới"} → chỉ đổi tên, description giữ nguyên
      - Gửi {} (rỗng) → báo lỗi 400
    """
    project = get_active_project_or_404(project_id, db)
    require_owner_or_403(project_id, current_user.id, db)

    # Lấy các trường được gửi lên (exclude_unset=True bỏ qua trường không có trong request)
    updated_fields = data.model_dump(exclude_unset=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có trường nào được cập nhật. Hãy gửi ít nhất một trường.",
        )

    # Cập nhật từng trường vào đối tượng project
    for field, value in updated_fields.items():
        setattr(project, field, value)

    log_activity(
        project_id=project.id,
        actor_id=current_user.id,
        action=ActivityAction.PROJECT_UPDATED,
        detail=f"Cập nhật các trường: {', '.join(updated_fields.keys())}",
        db=db,
    )

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# PUT /projects/{project_id} — Cập nhật toàn bộ
# ---------------------------------------------------------------------------

@router.put("/{project_id}", response_model=ProjectResponse)
def replace_project(
    project_id: int,
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Thay thế toàn bộ thông tin dự án. Chỉ OWNER mới được thực hiện.

    PUT — yêu cầu gửi đủ tất cả các trường (name bắt buộc, description tuỳ chọn).
    Khác PATCH: nếu không gửi description thì description sẽ bị đặt về None.
    """
    project = get_active_project_or_404(project_id, db)
    require_owner_or_403(project_id, current_user.id, db)

    project.name = data.name
    project.description = data.description

    log_activity(
        project_id=project.id,
        actor_id=current_user.id,
        action=ActivityAction.PROJECT_UPDATED,
        detail="Cập nhật toàn bộ thông tin dự án (PUT)",
        db=db,
    )

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id} — Xóa mềm dự án
# ---------------------------------------------------------------------------

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xóa mềm (soft delete) dự án. Chỉ OWNER mới được thực hiện.

    Sau khi xóa:
      - is_deleted = True
      - deleted_at = thời điểm hiện tại
      - Dữ liệu vẫn còn trong DB, chỉ không hiển thị qua API nữa
      - Mọi GET /projects/{id} sau đó sẽ trả về 404

    HTTP 204 No Content — không trả về body.
    """
    project = get_active_project_or_404(project_id, db)
    require_owner_or_403(project_id, current_user.id, db)

    # Đánh dấu đã xóa — không xóa dòng khỏi database
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)

    log_activity(
        project_id=project.id,
        actor_id=current_user.id,
        action=ActivityAction.PROJECT_DELETED,
        detail=f"Xóa mềm dự án '{project.name}'",
        db=db,
    )

    db.commit()
    # Không return gì — FastAPI tự trả 204 No Content

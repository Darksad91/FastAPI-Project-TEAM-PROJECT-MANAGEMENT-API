from enum import Enum


class UserRole(str, Enum):
    """Vai trò của người dùng trong hệ thống."""
    USER = "USER"
    ADMIN = "ADMIN"


class ProjectMemberRole(str, Enum):
    """Vai trò của thành viên trong một dự án."""
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class TaskStatus(str, Enum):
    """Trạng thái của task."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(str, Enum):
    """Mức độ ưu tiên của task."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActivityAction(str, Enum):
    """Loại hành động được ghi vào lịch sử thao tác (activity log)."""
    PROJECT_CREATED = "PROJECT_CREATED"  # Tạo dự án mới
    PROJECT_UPDATED = "PROJECT_UPDATED"  # Cập nhật thông tin dự án
    PROJECT_DELETED = "PROJECT_DELETED"  # Xóa mềm dự án
    MEMBER_ADDED    = "MEMBER_ADDED"     # Thêm thành viên vào dự án
    MEMBER_REMOVED  = "MEMBER_REMOVED"   # Xóa thành viên khỏi dự án

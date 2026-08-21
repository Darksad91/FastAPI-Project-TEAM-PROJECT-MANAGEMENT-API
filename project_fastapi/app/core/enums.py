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

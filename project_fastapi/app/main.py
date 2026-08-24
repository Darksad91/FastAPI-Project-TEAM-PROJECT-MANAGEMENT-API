from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import engine, Base
from app.models import users, projects, project_members, tasks  # import để SQLAlchemy nhận diện các bảng
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tạo tất cả các bảng trong Database nếu chưa có.
    # Lưu ý: dự án thực tế lớn thường dùng Alembic để quản lý migration thay vì dùng cách này.
    Base.metadata.create_all(bind=engine)
    yield


# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="TEAM PROJECT MANAGEMENT API",
    description="Ứng dụng quản lý thành viên trong nhóm dự án",
    version="1.0.0",
    lifespan=lifespan,
)

# Đăng ký các router
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health_check():
    """Kiểm tra server có đang chạy không."""
    return {"status": "ok"}

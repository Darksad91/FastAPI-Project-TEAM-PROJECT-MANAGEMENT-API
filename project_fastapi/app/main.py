from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.routers import auth, protected, cors_demo, files
# Import cả 2 model để SQLAlchemy nhận biết và tạo đủ bảng khi khởi động
from app.models import user, role  # noqa: F401


# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Project cuối khoá: TEAM PROJECT MANAGEMENT API",
    description="Ứng dụng quản lý thành viên trong nhóm",
    version="1.0.0"
)

# Tạo tất cả các bảng trong Database (nếu chưa có)
# Lưu ý: Trong thực tế dự án lớn thường dùng thư viện Alembic để quản lý database migration thay vì tạo trực tiếp.
Base.metadata.create_all(bind=engine)
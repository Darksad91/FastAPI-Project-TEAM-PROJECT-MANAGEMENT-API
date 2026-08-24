from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.database import engine, Base
from app.models import users, projects, project_members, tasks, activity_logs
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.project_members import router as project_members_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tạo tất cả các bảng trong Database (nếu chưa có).
    # Lưu ý: Trong thực tế dự án lớn thường dùng Alembic để quản lý migration.
    Base.metadata.create_all(bind=engine)
    yield


# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Project cuối khoá: TEAM PROJECT MANAGEMENT API",
    description="Ứng dụng quản lý thành viên trong nhóm",
    version="1.0.0",
    lifespan=lifespan,
)

# Đăng ký các router — mỗi router quản lý một nhóm endpoint
app.include_router(auth_router)           # /auth/...
app.include_router(users_router)          # /users/...
app.include_router(projects_router)       # /projects/...
app.include_router(project_members_router)  # /projects/{id}/members/...


@app.get("/health")
def health_check():
    """Kiểm tra server có đang chạy không. Trả về {"status": "ok"} nếu bình thường."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Xử lý lỗi toàn cục — áp dụng cho toàn bộ ứng dụng
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Bắt tất cả HTTPException được raise trong ứng dụng và định dạng lại response.

    Mặc định FastAPI trả về: {"detail": "..."}
    Handler này đổi thành:    {"status_code": 404, "detail": "..."}
    để response luôn nhất quán và dễ xử lý ở phía client.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Bắt lỗi validation của Pydantic khi client gửi dữ liệu sai định dạng.

    Ví dụ: gửi email không hợp lệ, password quá ngắn, thiếu trường bắt buộc...
    FastAPI tự động gọi handler này trước khi request vào đến router.

    Trả về HTTP 422 Unprocessable Entity với danh sách lỗi chi tiết.
    """
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "detail": exc.errors(),
        },
    )

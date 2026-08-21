from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.db.database import engine, Base
from app.models import users, projects, project_members, tasks
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router


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

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "detail": exc.detail},
    )

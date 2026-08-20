from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.db.database import engine, Base
from app.models import users, projects, project_members, tasks

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Project cuối khoá: TEAM PROJECT MANAGEMENT API",
    description="Ứng dụng quản lý thành viên trong nhóm",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "detail": exc.detail},
    )

# Tạo tất cả các bảng trong Database (nếu chưa có)
# Lưu ý: Trong thực tế dự án lớn thường dùng thư viện Alembic để quản lý database migration thay vì tạo trực tiếp.
Base.metadata.create_all(bind=engine)

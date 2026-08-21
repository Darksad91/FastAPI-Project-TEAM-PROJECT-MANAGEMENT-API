from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # --- Cấu hình Database ---
    # Đọc từ biến môi trường DATABASE_URL trong file .env
    DATABASE_URL: str

    # --- Cấu hình JWT ---
    # Đọc từ biến môi trường SECRET_KEY trong file .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Cấu hình CORS ---
    # Đọc từ biến môi trường ALLOWED_ORIGINS trong file .env (dạng JSON list)
    # ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        # Chỉ định file .env để pydantic-settings tự động đọc
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Bỏ qua các biến môi trường không được khai báo trong Settings
        extra = "ignore"


# Khởi tạo một instance duy nhất (Singleton) dùng cho toàn bộ ứng dụng
# Các file khác chỉ cần: from app.core.config import settings
settings = Settings()

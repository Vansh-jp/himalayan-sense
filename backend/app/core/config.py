from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "HimalayaSense"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./himalayasense.db"

    # JWT & Auth
    JWT_SECRET: str = "dev_jwt_secret_key_himalayasense_uttarakhand_secure_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Weather
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"

    # File uploads
    UPLOAD_DIR: str = "./uploads"

    # SMTP Notifications
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_FROM_EMAIL: str = "no-reply@himalayasense.local"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Background tasks
    ENABLE_SCHEDULER: bool = False
    WEATHER_SYNC_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    DATABASE_URL: str
    JWT_SECRET_KEY: str = "8a3d76e48bcfe2389d311029c74ab901f481c9a6ec89f81d1192fa29a1ee35b3"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours
    
    @property
    def clean_database_url(self) -> str:
        url = self.DATABASE_URL.strip()
        # Fix the duplicate schema prefix
        if url.startswith("postgresql+asyncpg://postgresql://"):
            url = url.replace("postgresql+asyncpg://postgresql://", "postgresql+asyncpg://")
        # Ensure it has the +asyncpg driver prefix for SQLAlchemy AsyncSession
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://")
            
        # Strip sslmode parameters to prevent asyncpg unexpected keyword argument error
        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0]
        elif "&sslmode=" in url:
            url = url.split("&sslmode=")[0]
            
        return url

settings = Settings()

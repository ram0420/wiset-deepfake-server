# 설정 관리 (BaseConfig, DevConfig, ProdConfig)from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

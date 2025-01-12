import os
from dotenv import load_dotenv

from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DB_HOST: str = os.getenv("POSTGRES_HOST")
    DOCKER_DB_HOST: str = os.getenv("POSTGRES_DOCKER_HOST")
    DB_PORT: int = os.getenv("POSTGRES_PORT")
    DOCKER_DB_PORT: int = os.getenv("POSTGRES_DOCKER_PORT")
    DB_NAME: str = os.getenv("POSTGRES_DB")
    DB_USER: str = os.getenv("POSTGRES_USER")
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")


settings = Settings()


def get_db_url():
    return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


# Получение DB_URL для докера:
def get_docker_db_url():
    return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DOCKER_DB_HOST}:{settings.DOCKER_DB_PORT}/{settings.DB_NAME}"

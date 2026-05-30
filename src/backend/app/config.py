import os
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url: str) -> str:
    # Render (and Heroku) provide postgres:// — psycopg v3 requires postgresql+psycopg://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _fix_db_url(os.environ["DATABASE_URL"])
    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    ALLOWED_EMAILS = os.getenv("ALLOWED_EMAILS", "").split(",")
    FIREBASE_PROJECT_ID = os.environ["FIREBASE_PROJECT_ID"]


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


_configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(name="development"):
    return _configs.get(name, DevelopmentConfig)

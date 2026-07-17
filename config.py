import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Application configuration loaded from environment variables when available."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///university.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

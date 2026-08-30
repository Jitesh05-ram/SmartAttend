import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# INSTANCE DIRECTORY
# ============================================================
# Render needs a writable location for SQLite.
# This directory will be created automatically.

INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = INSTANCE_DIR / "smartattend.db"


class Config:

    # ========================================================
    # FLASK
    # ========================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "smartattend-development-secret-key"
    )

    # ========================================================
    # DATABASE
    # ========================================================

    DATABASE_URL = os.getenv("DATABASE_URL")

    # Render PostgreSQL sometimes provides postgres://
    # SQLAlchemy expects postgresql://

    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{DB_PATH}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ========================================================
    # EMAIL
    # ========================================================

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            "587"
        )
    )

    MAIL_USE_TLS = (
        os.getenv(
            "MAIL_USE_TLS",
            "True"
        ).lower() == "true"
    )

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        ""
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD",
        ""
    )

    # ========================================================
    # EMAIL VERIFICATION SWITCH
    # ========================================================

    REQUIRE_EMAIL_VERIFICATION = (
        os.getenv(
            "REQUIRE_EMAIL_VERIFICATION",
            "False"
        ).lower() == "true"
    )

    # ========================================================
    # FILE UPLOAD
    # ========================================================

    MAX_CONTENT_LENGTH = (
        16 * 1024 * 1024
    )

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "backend" / "uploads")
    )

    # ========================================================
    # ALLOWED FILE EXTENSIONS
    # ========================================================

    ALLOWED_EXTENSIONS = {
        "csv",
        "xlsx",
        "xls"
    }
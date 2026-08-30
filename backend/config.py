import os

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE DIRECTORY (absolute path to project root, e.g. SmartAttend/)
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(BASE_DIR, "database", "smartattend.db")


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

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
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
    # Gmail SMTP isn't configured yet, so verification emails
    # can't be delivered. Set this to True once MAIL_USERNAME /
    # MAIL_PASSWORD above are filled in with a working Gmail
    # App Password, to require email verification again.

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
        "backend/uploads"
    )

    # ========================================================
    # ALLOWED FILE EXTENSIONS
    # ========================================================

    ALLOWED_EXTENSIONS = {
        "csv",
        "xlsx",
        "xls"
    }
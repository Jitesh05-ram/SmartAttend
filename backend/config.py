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
    # SESSION / COOKIE SECURITY
    # ========================================================
    # HTTPONLY blocks JavaScript from reading the session cookie
    # (mitigates XSS-based session theft). SAMESITE=Lax stops the
    # cookie being sent on most cross-site requests (CSRF defense
    # in depth, on top of Flask-WTF's CSRF tokens). SECURE should
    # be True in production once the app is served over HTTPS —
    # controlled by an env var so local HTTP development still
    # works without the cookie being silently dropped.

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14  # 14 days

    # ========================================================
    # DEBUG MODE
    # ========================================================
    # Off by default. Set FLASK_DEBUG=True in .env only for local
    # development — debug mode must never run in production (it
    # exposes an interactive debugger that allows remote code
    # execution to anyone who can reach the server).

    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

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
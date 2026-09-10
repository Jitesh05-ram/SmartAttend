from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect


# ============================================================
# DATABASE
# ============================================================

db = SQLAlchemy()


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."


# ============================================================
# MAIL
# ============================================================

mail = Mail()


# ============================================================
# CSRF PROTECTION
# ============================================================
# Protects every session-based (cookie) POST/PUT/PATCH/DELETE
# form submission in the app. The token-authenticated REST API
# blueprint (backend/routes/api.py) is exempted in app.py since
# it doesn't use cookies/sessions and is protected by Bearer
# tokens instead.

csrf = CSRFProtect()
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail


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
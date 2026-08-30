from flask import Flask, app

from backend.config import Config
from backend import db, login_manager, mail


def create_app():

    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    app.config.from_object(Config)

    # ========================================================
    # INITIALIZE EXTENSIONS
    # ========================================================

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # ========================================================
    # LOGIN MANAGER
    # ========================================================

    @login_manager.user_loader
    def load_user(user_id):

        from backend.models.user import User

        try:
            return db.session.get(
                User,
                int(user_id)
            )

        except (ValueError, TypeError):

            return None

    # ========================================================
    # BLUEPRINTS
    # ========================================================

    from backend.routes.students import student_bp
    from backend.routes.auth import auth_bp
    from backend.routes.subjects import subject_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.attendance import attendance_bp
    from backend.routes.reports import reports_bp
    from backend.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # ========================================================
    # DATABASE
    # ========================================================

    with app.app_context():

        from backend.models.user import User
        from backend.models.student import Student
        from backend.models.subject import Subject
        from backend.models.attendance import Attendance

        db.create_all()

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    @app.route("/health")
    def health():

        return {
            "success": True,
            "message": "SmartAttend backend is running."
        }

    # ========================================================
    # RETURN APP
    # ========================================================

    return app


# ============================================================
# CREATE APPLICATION
# ============================================================

app = create_app()


# ============================================================
# RUN DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
from flask import Flask, app

from backend.config import Config
from backend import db, login_manager, mail, csrf


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
    csrf.init_app(app)

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
    from backend.routes.batches import batch_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(batch_bp)

    # --------------------------------------------------------
    # The /api/* blueprint authenticates with a Bearer token
    # (see backend/utils/auth_token.py), not a session cookie,
    # so it isn't vulnerable to CSRF and is exempted here.
    #
    # Only the JSON /api/auth/* endpoints on auth_bp are also
    # exempted individually — they're stateless (no session
    # cookie involved), unlike the web login/register/reset
    # forms on the same blueprint, which stay protected.
    # --------------------------------------------------------

    csrf.exempt(api_bp)
    csrf.exempt(app.view_functions["auth.api_login"])
    csrf.exempt(app.view_functions["auth.api_register"])
    csrf.exempt(app.view_functions["auth.api_logout"])

    # ========================================================
    # DATABASE
    # ========================================================

    with app.app_context():

        from backend.models.user import User
        from backend.models.student import Student
        from backend.models.subject import Subject
        from backend.models.attendance import Attendance
        from backend.models.batch import Batch

        db.create_all()

        from backend.utils.migrate_schema import run_startup_migration
        run_startup_migration()

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

    # host="0.0.0.0" (not "127.0.0.1") so the server is reachable
    # from an Android emulator (10.0.2.2) or a real phone on the
    # same Wi-Fi network — 127.0.0.1 only accepts connections
    # from this same PC.
    app.run(
        debug=app.config.get("DEBUG", False),
        host="0.0.0.0",
        port=5000
    )
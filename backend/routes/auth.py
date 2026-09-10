from datetime import datetime, timedelta, timezone
import secrets

from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    g,
    current_app
)

from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required
)

from backend import db
from backend.models.user import User
from backend.models.batch import Batch
from backend.utils.auth_token import token_required


auth_bp = Blueprint("auth", __name__)


def _seed_default_batches(user_id):
    """
    Give a brand-new account a sensible starting set of batches so
    it isn't an empty slate. Fully editable/deletable afterwards
    from the Manage Batch page — this is just a convenience default.
    """
    for default_name in ("FY", "SY", "TY"):
        db.session.add(Batch(user_id=user_id, name=default_name))
    db.session.commit()


# ============================================================
# HOME
# ============================================================

@auth_bp.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))

        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password:
        flash(
            "Name, email and password are required.",
            "danger"
        )
        return render_template("register.html")

    if password != confirm_password:
        flash(
            "Passwords do not match.",
            "danger"
        )
        return render_template("register.html")

    if len(password) < 8:
        flash(
            "Password must be at least 8 characters.",
            "danger"
        )
        return render_template("register.html")

    existing_user = User.query.filter_by(
        email=email
    ).first()

    verification_required = current_app.config.get(
        "REQUIRE_EMAIL_VERIFICATION", False
    )

    if existing_user:

        if existing_user.is_verified:

            flash(
                "An account with this email already exists.",
                "warning"
            )

            return render_template("register.html")

        existing_user.name = name
        existing_user.set_password(password)

        if verification_required:

            token = secrets.token_urlsafe(32)

            existing_user.verification_token = token
            existing_user.verification_token_expiry = (
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            )

            db.session.commit()

            flash(
                "Account updated. Please verify your email.",
                "success"
            )

        else:

            existing_user.is_verified = True
            db.session.commit()

            flash(
                "Account updated. You can log in now.",
                "success"
            )

        return redirect(url_for("auth.login"))

    user = User(
        name=name,
        email=email,
        is_verified=not verification_required,
        verification_token=(
            secrets.token_urlsafe(32) if verification_required else None
        ),
        verification_token_expiry=(
            datetime.now(timezone.utc) + timedelta(hours=24)
            if verification_required else None
        )
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    _seed_default_batches(user.id)

    if not verification_required:

        flash(
            "Registration successful. You can log in now.",
            "success"
        )

        return redirect(url_for("auth.login"))

    from backend.services.email_service import send_verification_email

    try:
        send_verification_email(user)
        flash(
            "Registration successful. Please check your email to verify your account.",
            "success"
        )
    except Exception as e:
        flash(
            "Account created, but the verification email could not be sent. "
            "Please contact support or try again later.",
            "warning"
        )
        print("EMAIL SEND ERROR:", e)

    return redirect(url_for("auth.login"))


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))

        return render_template("login.html")

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        flash(
            "Email and password are required.",
            "danger"
        )

        return render_template("login.html")

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None:

        flash(
            "Invalid email or password.",
            "danger"
        )

        return render_template("login.html")

    if not user.is_verified and current_app.config.get(
        "REQUIRE_EMAIL_VERIFICATION", False
    ):

        flash(
            "Please verify your email before logging in.",
            "warning"
        )

        return render_template("login.html")

    if not user.check_password(password):

        flash(
            "Invalid email or password.",
            "danger"
        )

        return render_template("login.html")

    remember_me = request.form.get("remember") == "on"

    login_user(
        user,
        remember=remember_me
    )

    flash(
        "Login successful.",
        "success"
    )

    return redirect(
        url_for("dashboard.dashboard")
    )


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# ============================================================
# EMAIL VERIFICATION
# ============================================================

@auth_bp.route("/verify-email/<token>")
def verify_email_web(token):

    user = User.query.filter_by(
        verification_token=token
    ).first()

    if not user:

        return """
        <h3>Invalid or already used verification link.</h3>
        """

    if user.is_verified:

        return """
        <h3>Email is already verified.</h3>
        <a href="/login">Go to Login</a>
        """

    expiry = user.verification_token_expiry

    if not expiry:

        return """
        <h3>Verification link is invalid.</h3>
        """

    if expiry.tzinfo is None:
        expiry = expiry.replace(
            tzinfo=timezone.utc
        )

    if datetime.now(timezone.utc) > expiry:

        return """
        <h3>Verification link has expired.</h3>
        """

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None

    db.session.commit()

    return """
    <h2>Email verified successfully!</h2>
    <p>You can now log in to SmartAttend.</p>
    <a href="/login">Go to Login</a>
    """


# ============================================================
# API LOGIN
# ============================================================

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():

    data = request.get_json(
        silent=True
    ) or {}

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if not user.is_verified and current_app.config.get(
        "REQUIRE_EMAIL_VERIFICATION", False
    ):

        return jsonify({
            "success": False,
            "message": "Please verify your email before logging in."
        }), 403

    if not user.check_password(password):

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # Issue a fresh API token for this session (mobile/API clients
    # use this instead of a browser session cookie).
    user.api_token = secrets.token_urlsafe(32)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": user.api_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200


# ============================================================
# API REGISTER
# ============================================================

@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Name, email and password are required."
        }), 400

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters."
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    verification_required = current_app.config.get(
        "REQUIRE_EMAIL_VERIFICATION", False
    )

    user = User(
        name=name,
        email=email,
        is_verified=not verification_required,
        verification_token=(
            secrets.token_urlsafe(32) if verification_required else None
        ),
        verification_token_expiry=(
            datetime.now(timezone.utc) + timedelta(hours=24)
            if verification_required else None
        )
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    _seed_default_batches(user.id)

    if not verification_required:
        return jsonify({
            "success": True,
            "message": "Registration successful. You can log in now."
        }), 201

    from backend.services.email_service import send_verification_email

    try:
        send_verification_email(user)
    except Exception as e:
        print("EMAIL SEND ERROR:", e)

    return jsonify({
        "success": True,
        "message": "Registration successful. Please verify your email before logging in."
    }), 201


# ============================================================
# API LOGOUT
# ============================================================

@auth_bp.route("/api/auth/logout", methods=["POST"])
@token_required
def api_logout():

    g.current_api_user.api_token = None
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


# ============================================================
# FORGOT PASSWORD
# ============================================================

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email", "").strip().lower()

    if not email:
        flash("Please enter your email address.", "danger")
        return render_template("forgot_password.html")

    user = User.query.filter_by(email=email).first()

    # Always show the same message whether or not the account
    # exists, so this endpoint can't be used to check which
    # emails are registered.
    generic_message = (
        "If an account exists for that email, a password reset "
        "link has been sent."
    )

    if not user:
        flash(generic_message, "info")
        return render_template("forgot_password.html")

    user.reset_token = secrets.token_urlsafe(32)
    user.reset_token_expiry = (
        datetime.now(timezone.utc) + timedelta(hours=1)
    )

    db.session.commit()

    from backend.services.email_service import send_password_reset_email

    try:
        send_password_reset_email(user)
        flash(generic_message, "info")
    except Exception as e:
        # SMTP not configured / failed — print the link so the
        # account owner can still reset in a dev environment.
        reset_link = url_for(
            "auth.reset_password", token=user.reset_token, _external=True
        )
        print("PASSWORD RESET EMAIL FAILED:", e)
        print("RESET LINK (dev fallback):", reset_link)
        flash(generic_message, "info")

    return render_template("forgot_password.html")


# ============================================================
# RESET PASSWORD
# ============================================================

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    expiry = user.reset_token_expiry
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if not expiry or datetime.now(timezone.utc) > expiry:
        flash("This reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return render_template("reset_password.html", token=token)

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return render_template("reset_password.html", token=token)

    user.set_password(password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.session.commit()

    flash("Password reset successful. Please log in.", "success")
    return redirect(url_for("auth.login"))


# ============================================================
# VERIFY EMAIL PAGE
# ============================================================

@auth_bp.route("/verify-email")
def verify_email_page():

    return render_template(
        "verify_email.html"
    )
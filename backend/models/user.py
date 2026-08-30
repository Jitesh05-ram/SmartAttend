from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from backend import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # ========================================================
    # PASSWORD
    # ========================================================

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # ========================================================
    # EMAIL VERIFICATION
    # ========================================================

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    verification_token = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )

    verification_token_expiry = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ========================================================
    # PASSWORD RESET
    # ========================================================

    reset_token = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )

    reset_token_expiry = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ========================================================
    # API TOKEN (for the Android app / REST API clients)
    # ========================================================

    api_token = db.Column(
        db.String(255),
        unique=True,
        nullable=True,
        index=True
    )

    # ========================================================
    # CREATED DATE
    # ========================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    students = db.relationship(
        "Student",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    subjects = db.relationship(
        "Subject",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    attendances = db.relationship(
        "Attendance",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # ========================================================
    # PASSWORD METHODS
    # ========================================================

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            f"<User {self.email}>"
        )
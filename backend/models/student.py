from datetime import datetime, timezone

from backend import db


class Student(db.Model):

    __tablename__ = "students"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # OWNER / TEACHER
    # ========================================================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ========================================================
    # STUDENT INFORMATION
    # ========================================================

    roll_number = db.Column(
        db.String(50),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    batch = db.Column(
        db.String(50),
        nullable=True
    )

    year = db.Column(
        db.String(20),
        nullable=True
    )

    email = db.Column(
        db.String(255),
        nullable=True
    )

    phone = db.Column(
        db.String(30),
        nullable=True
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

    owner = db.relationship(
        "User",
        back_populates="students"
    )

    attendances = db.relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    # ========================================================
    # UNIQUE CONSTRAINT
    # ========================================================
    # The same teacher cannot have two students with the
    # same roll number.

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "roll_number",
            name="unique_student_roll_per_user"
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            f"<Student {self.roll_number} - {self.name}>"
        )
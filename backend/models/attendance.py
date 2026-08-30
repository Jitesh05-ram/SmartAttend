from datetime import datetime, timezone

from backend import db


class Attendance(db.Model):

    __tablename__ = "attendances"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # TEACHER / OWNER
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
    # STUDENT
    # ========================================================

    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "students.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ========================================================
    # SUBJECT
    # ========================================================

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "subjects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ========================================================
    # ATTENDANCE DATE
    # ========================================================

    date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    # ========================================================
    # STATUS
    # ========================================================

    status = db.Column(
        db.String(20),
        nullable=False
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
        back_populates="attendances"
    )

    student = db.relationship(
        "Student",
        back_populates="attendances"
    )

    subject = db.relationship(
        "Subject",
        back_populates="attendances"
    )

    # ========================================================
    # UNIQUE CONSTRAINT
    # ========================================================
    # A student can only have ONE attendance record per
    # subject per date. The route also checks this before
    # inserting (upsert), but this is the database-level
    # safety net.

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "subject_id",
            "date",
            name="unique_attendance_per_day"
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            f"<Attendance student={self.student_id} "
            f"subject={self.subject_id} "
            f"date={self.date} "
            f"status={self.status}>"
        )
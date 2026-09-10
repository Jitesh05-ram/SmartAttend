from datetime import datetime, timezone

from backend import db


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    code = db.Column(
        db.String(50),
        nullable=True
    )

    # ========================================================
    # BATCH
    # ========================================================
    # Teacher-defined batches (see backend/models/batch.py). A
    # subject with no batch set applies to all batches.

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "batches.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    batch = db.relationship(
        "Batch",
        back_populates="subjects"
    )

    # ========================================================
    # ACADEMIC YEAR
    # ========================================================
    # A plain, manually-typed calendar year (e.g. 2026). This is
    # independent of the batch above — just a number the teacher
    # enters directly, not a managed list.

    academic_year = db.Column(
        db.Integer,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    owner = db.relationship(
        "User",
        back_populates="subjects"
    )

    attendances = db.relationship(
        "Attendance",
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "name",
            name="unique_subject_per_user"
        ),
    )

    def __repr__(self):
        return f"<Subject {self.name}>"

from datetime import datetime, timezone

from backend import db


class Batch(db.Model):
    """
    A teacher-defined batch, e.g. "FY", "SY", "TY", "1st Year",
    "Diploma", "Final Year", "2026 Batch". Each teacher manages
    their own independent list of batches and assigns students /
    subjects to them.

    This is separate from the plain numeric "Academic Year" field
    (e.g. 2026) that teachers can type directly on a student or
    subject — that field is just a number, not a managed entity.
    """

    __tablename__ = "batches"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(50),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    owner = db.relationship(
        "User",
        back_populates="batches"
    )

    students = db.relationship(
        "Student",
        back_populates="assigned_batch"
    )

    subjects = db.relationship(
        "Subject",
        back_populates="batch"
    )

    # ========================================================
    # UNIQUE CONSTRAINT
    # ========================================================
    # The same teacher cannot create two batches with the same
    # name (case-sensitive as typed, e.g. "FY" and "fy" are
    # treated as distinct since teachers may want that level
    # of control over labels).

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "name",
            name="unique_batch_per_user"
        ),
    )

    def __repr__(self):
        return f"<Batch {self.name}>"

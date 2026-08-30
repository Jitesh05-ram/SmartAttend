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
    
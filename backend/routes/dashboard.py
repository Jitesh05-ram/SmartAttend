from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from backend import db
from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance
from backend.models.batch import Batch


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard_bp.route("/")
@login_required
def dashboard():

    student_count = Student.query.filter_by(
        user_id=current_user.id
    ).count()

    subject_count = Subject.query.filter_by(
        user_id=current_user.id
    ).count()

    attendance_count = Attendance.query.filter_by(
        user_id=current_user.id
    ).count()

    # --------------------------------------------------------
    # Students-per-batch breakdown — one query, grouped, instead
    # of a count() call per batch. Teacher-defined batches, so the
    # dashboard shows however many batches this teacher has set up.
    # --------------------------------------------------------

    batches = Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.created_at.asc()).all()

    batch_rows = db.session.query(
        Student.batch_id, db.func.count(Student.id)
    ).filter_by(
        user_id=current_user.id
    ).group_by(
        Student.batch_id
    ).all()

    batch_row_counts = dict(batch_rows)

    batch_counts = [
        {"id": batch.id, "name": batch.name, "count": batch_row_counts.get(batch.id, 0)}
        for batch in batches
    ]

    unassigned_count = batch_row_counts.get(None, 0)

    # --------------------------------------------------------
    # Today's attendance snapshot
    # --------------------------------------------------------

    today = date.today()

    today_records = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).all()

    today_present = sum(1 for r in today_records if r.status == "Present")
    today_absent = sum(1 for r in today_records if r.status == "Absent")
    today_total = len(today_records)
    today_percentage = (
        round((today_present / today_total) * 100)
        if today_total else None
    )

    return render_template(
        "dashboard.html",
        student_count=student_count,
        subject_count=subject_count,
        attendance_count=attendance_count,
        batch_counts=batch_counts,
        unassigned_count=unassigned_count,
        today_present=today_present,
        today_absent=today_absent,
        today_total=today_total,
        today_percentage=today_percentage
    )
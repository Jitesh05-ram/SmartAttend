from flask import Blueprint, render_template
from flask_login import login_required, current_user

from backend import db
from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance


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

    return render_template(
        "dashboard.html",
        student_count=student_count,
        subject_count=subject_count,
        attendance_count=attendance_count
    )
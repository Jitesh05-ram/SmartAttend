from datetime import datetime, date as date_cls

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from backend import db
from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)


# ============================================================
# MARK ATTENDANCE (GET: show form / load students, POST: save)
# ============================================================

@attendance_bp.route("/mark", methods=["GET", "POST"])
@login_required
def mark_attendance():

    subjects = Subject.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subject.name.asc()
    ).all()

    if request.method == "POST":

        subject_id = request.form.get("subject_id", type=int)
        date_str = request.form.get("date", "")

        if not subject_id or not date_str:
            flash("Subject and date are required.", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        subject = Subject.query.filter_by(
            id=subject_id,
            user_id=current_user.id
        ).first()

        if not subject:
            flash("Invalid subject selected.", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        try:
            attendance_date = datetime.strptime(
                date_str, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        students = Student.query.filter_by(
            user_id=current_user.id
        ).all()

        saved_count = 0

        for student in students:

            status = request.form.get(f"status_{student.id}")

            if status not in ("Present", "Absent"):
                continue

            # ----------------------------------------------
            # UPSERT: update existing record for this
            # student + subject + date, or create a new one.
            # This is what prevents duplicate attendance rows.
            # ----------------------------------------------

            existing = Attendance.query.filter_by(
                user_id=current_user.id,
                student_id=student.id,
                subject_id=subject_id,
                date=attendance_date
            ).first()

            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(
                    user_id=current_user.id,
                    student_id=student.id,
                    subject_id=subject_id,
                    date=attendance_date,
                    status=status
                ))

            saved_count += 1

        db.session.commit()

        flash(
            f"Attendance saved for {saved_count} student(s) "
            f"({subject.name}, {attendance_date.strftime('%d-%m-%Y')}).",
            "success"
        )

        return redirect(
            url_for(
                "attendance.mark_attendance",
                subject_id=subject_id,
                date=date_str
            )
        )

    # ================================================================
    # GET — show the picker, and if subject_id + date are given,
    # load the student list with any existing statuses pre-filled.
    # ================================================================

    subject_id = request.args.get("subject_id", type=int)
    date_str = request.args.get("date", "")

    students = []
    selected_subject = None
    existing_map = {}

    if subject_id and date_str:

        selected_subject = Subject.query.filter_by(
            id=subject_id,
            user_id=current_user.id
        ).first()

        if not selected_subject:
            flash("Invalid subject selected.", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        try:
            attendance_date = datetime.strptime(
                date_str, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        students = Student.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Student.roll_number.asc()
        ).all()

        existing_records = Attendance.query.filter_by(
            user_id=current_user.id,
            subject_id=subject_id,
            date=attendance_date
        ).all()

        existing_map = {
            record.student_id: record.status
            for record in existing_records
        }

    return render_template(
        "mark_attendance.html",
        subjects=subjects,
        students=students,
        selected_subject=selected_subject,
        selected_date=date_str,
        existing_map=existing_map,
        today=date_cls.today().strftime("%Y-%m-%d")
    )


# ============================================================
# ATTENDANCE HISTORY (with filters)
# ============================================================

@attendance_bp.route("/history")
@login_required
def history():

    # ------------------------------------------------------
    # Read filters from the query string
    # ------------------------------------------------------

    filter_date = request.args.get("date", "")
    filter_subject_id = request.args.get("subject_id", type=int)
    filter_student_id = request.args.get("student_id", type=int)
    filter_status = request.args.get("status", "")
    filter_batch = request.args.get("batch", "")
    filter_year = request.args.get("year", "")

    query = Attendance.query.filter_by(
        user_id=current_user.id
    ).join(
        Student, Attendance.student_id == Student.id
    ).join(
        Subject, Attendance.subject_id == Subject.id
    )

    if filter_date:
        try:
            parsed_date = datetime.strptime(
                filter_date, "%Y-%m-%d"
            ).date()
            query = query.filter(Attendance.date == parsed_date)
        except ValueError:
            pass

    if filter_subject_id:
        query = query.filter(Attendance.subject_id == filter_subject_id)

    if filter_student_id:
        query = query.filter(Attendance.student_id == filter_student_id)

    if filter_status in ("Present", "Absent"):
        query = query.filter(Attendance.status == filter_status)

    if filter_batch:
        query = query.filter(Student.batch == filter_batch)

    if filter_year:
        query = query.filter(Student.year == filter_year)

    records = query.order_by(
        Attendance.date.desc(),
        Student.roll_number.asc()
    ).limit(500).all()

    # ------------------------------------------------------
    # Data for the filter dropdowns
    # ------------------------------------------------------

    subjects = Subject.query.filter_by(
        user_id=current_user.id
    ).order_by(Subject.name.asc()).all()

    students = Student.query.filter_by(
        user_id=current_user.id
    ).order_by(Student.roll_number.asc()).all()

    batches = sorted({
        s.batch for s in students if s.batch
    })

    years = sorted({
        s.year for s in students if s.year
    })

    return render_template(
        "attendance_history.html",
        records=records,
        subjects=subjects,
        students=students,
        batches=batches,
        years=years,
        filters={
            "date": filter_date,
            "subject_id": filter_subject_id,
            "student_id": filter_student_id,
            "status": filter_status,
            "batch": filter_batch,
            "year": filter_year,
        }
    )

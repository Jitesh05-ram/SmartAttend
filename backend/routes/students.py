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


student_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/students"
)


# ============================================================
# STUDENT LIST
# ============================================================

@student_bp.route("/")
@login_required
def student_list():

    students = Student.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Student.roll_number.asc()
    ).all()

    return render_template(
        "students.html",
        students=students
    )


# ============================================================
# ADD STUDENT
# ============================================================

@student_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_student_page():

    if request.method == "GET":
        return render_template("add_student.html")

    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch", "").strip()
    year = request.form.get("year", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not roll_number or not name:
        flash("Roll number and name are required.", "danger")
        return render_template("add_student.html")

    existing_student = Student.query.filter_by(
        user_id=current_user.id,
        roll_number=roll_number
    ).first()

    if existing_student:
        flash("A student with this roll number already exists.", "warning")
        return render_template("add_student.html")

    student = Student(
        user_id=current_user.id,
        roll_number=roll_number,
        name=name,
        batch=batch if batch else None,
        year=year if year else None,
        email=email if email else None,
        phone=phone if phone else None
    )

    db.session.add(student)
    db.session.commit()

    flash("Student added successfully.", "success")
    return redirect(url_for("students.student_list"))


# ============================================================
# EDIT STUDENT
# ============================================================

@student_bp.route("/edit/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student_page(student_id):

    student = Student.query.filter_by(
        id=student_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "GET":
        return render_template("edit_student.html", student=student)

    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch", "").strip()
    year = request.form.get("year", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not roll_number or not name:
        flash("Roll number and name are required.", "danger")
        return render_template("edit_student.html", student=student)

    duplicate = Student.query.filter(
        Student.user_id == current_user.id,
        Student.roll_number == roll_number,
        Student.id != student.id
    ).first()

    if duplicate:
        flash("Another student with this roll number already exists.", "warning")
        return render_template("edit_student.html", student=student)

    student.roll_number = roll_number
    student.name = name
    student.batch = batch if batch else None
    student.year = year if year else None
    student.email = email if email else None
    student.phone = phone if phone else None

    db.session.commit()

    flash("Student updated successfully.", "success")
    return redirect(url_for("students.student_list"))


# ============================================================
# DELETE STUDENT
# ============================================================

@student_bp.route("/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):

    student = Student.query.filter_by(
        id=student_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(student)
    db.session.commit()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("students.student_list"))


# ============================================================
# IMPORT STUDENTS (Excel/CSV) — page ready now, upload logic in Phase 2
# ============================================================

@student_bp.route("/import", methods=["GET"])
@login_required
def import_students_page():
    return render_template("import_student.html")


@student_bp.route("/import", methods=["POST"])
@login_required
def import_students():

    uploaded_file = request.files.get("file")

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please select a file to upload.", "danger")
        return redirect(url_for("students.import_students_page"))

    filename = uploaded_file.filename.lower()

    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
    ):
        flash(
            "Unsupported file type. Please upload a CSV, XLSX or XLS file.",
            "danger"
        )
        return redirect(url_for("students.import_students_page"))

    import pandas as pd

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        flash(f"Could not read the file: {e}", "danger")
        return redirect(url_for("students.import_students_page"))

    if df.empty:
        flash("The uploaded file has no data rows.", "warning")
        return redirect(url_for("students.import_students_page"))

    # Normalize column names (case/whitespace-insensitive)
    df.columns = [str(c).strip().lower() for c in df.columns]

    required_columns = {"roll_number", "name"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        flash(
            "The file is missing required column(s): "
            + ", ".join(sorted(missing_columns)),
            "danger"
        )
        return redirect(url_for("students.import_students_page"))

    # Existing roll numbers for this user, to catch duplicates
    # without hitting the database once per row.
    existing_roll_numbers = {
        s.roll_number
        for s in Student.query.filter_by(
            user_id=current_user.id
        ).with_entities(Student.roll_number).all()
    }

    seen_in_file = set()

    success_count = 0
    failed_rows = []
    new_students = []

    for index, row in df.iterrows():

        excel_row_number = index + 2  # header is row 1

        roll_number = str(row.get("roll_number", "")).strip()
        name = str(row.get("name", "")).strip()

        if roll_number in ("", "nan"):
            failed_rows.append(
                f"Row {excel_row_number}: missing roll_number."
            )
            continue

        if name in ("", "nan"):
            failed_rows.append(
                f"Row {excel_row_number} (roll {roll_number}): missing name."
            )
            continue

        if roll_number in existing_roll_numbers:
            failed_rows.append(
                f"Row {excel_row_number}: roll number '{roll_number}' "
                "already exists — skipped."
            )
            continue

        if roll_number in seen_in_file:
            failed_rows.append(
                f"Row {excel_row_number}: duplicate roll number "
                f"'{roll_number}' within the file — skipped."
            )
            continue

        def clean(value):
            text = str(value).strip()
            return text if text and text.lower() != "nan" else None

        new_students.append(Student(
            user_id=current_user.id,
            roll_number=roll_number,
            name=name,
            batch=clean(row.get("batch", "")),
            year=clean(row.get("year", "")),
            email=clean(row.get("email", "")),
            phone=clean(row.get("phone", ""))
        ))

        seen_in_file.add(roll_number)
        success_count += 1

    if new_students:
        db.session.bulk_save_objects(new_students)
        db.session.commit()

    if success_count:
        flash(
            f"Import complete: {success_count} student(s) added successfully, "
            f"{len(failed_rows)} row(s) failed.",
            "success" if not failed_rows else "warning"
        )
    else:
        flash(
            f"No students were imported. {len(failed_rows)} row(s) failed.",
            "danger"
        )

    if failed_rows:
        # Show up to 15 detailed error lines; summarize the rest.
        for line in failed_rows[:15]:
            flash(line, "warning")
        if len(failed_rows) > 15:
            flash(f"...and {len(failed_rows) - 15} more row(s) failed.", "warning")

    return redirect(url_for("students.student_list"))
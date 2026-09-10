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
from backend.models.batch import Batch
from backend.utils.sorting import order_students_by_roll_number


student_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/students"
)


# ============================================================
# HELPERS
# ============================================================

def _parse_batch_id(raw_value):
    """
    Turn a form value into an int batch_id, or None. Returns
    (batch_id, error_message). error_message is None on success.
    """

    raw_value = (raw_value or "").strip()

    if not raw_value:
        return None, None

    try:
        batch_id = int(raw_value)
    except ValueError:
        return None, "Invalid batch selected."

    batch = Batch.query.filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        return None, "Invalid batch selected."

    return batch_id, None


def _parse_academic_year(raw_value):
    """
    Turn a form value into an int academic year (e.g. 2026), or
    None. Returns (academic_year, error_message).
    """

    raw_value = (raw_value or "").strip()

    if not raw_value:
        return None, None

    try:
        academic_year = int(raw_value)
    except ValueError:
        return None, "Academic year must be a number."

    if academic_year < 1900 or academic_year > 2200:
        return None, "Academic year must be a valid year."

    return academic_year, None


# ============================================================
# STUDENT LIST
# ============================================================

@student_bp.route("/")
@login_required
def student_list():

    query = Student.query.filter_by(
        user_id=current_user.id
    )

    search = request.args.get("search", "").strip()
    batch_id_raw = request.args.get("batch_id", "").strip()
    batch = request.args.get("batch", "").strip()

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(like_pattern),
                Student.roll_number.ilike(like_pattern),
                Student.email.ilike(like_pattern)
            )
        )

    batch_id = None

    if batch_id_raw:
        try:
            batch_id = int(batch_id_raw)
            query = query.filter(Student.batch_id == batch_id)
        except ValueError:
            batch_id = None

    if batch:
        query = query.filter(Student.batch == batch)

    students = order_students_by_roll_number(query).all()

    all_batches = sorted({
        s.batch for s in Student.query.filter_by(user_id=current_user.id)
            .with_entities(Student.batch).all()
        if s.batch
    })

    batches = Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.created_at.asc()).all()

    return render_template(
        "students.html",
        students=students,
        all_batches=all_batches,
        filters={
            "search": search,
            "batch_id": batch_id,
            "batch": batch
        },
        batches=batches
    )


# ============================================================
# ADD STUDENT
# ============================================================

@student_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_student_page():

    batches = Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.created_at.asc()).all()

    if request.method == "GET":
        return render_template("add_student.html", batches=batches)

    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    batch_id, batch_error = _parse_batch_id(request.form.get("batch_id"))
    academic_year, year_error = _parse_academic_year(request.form.get("academic_year"))

    if not roll_number or not name:
        flash("Roll number and name are required.", "danger")
        return render_template("add_student.html", batches=batches)

    if batch_error:
        flash(batch_error, "danger")
        return render_template("add_student.html", batches=batches)

    if year_error:
        flash(year_error, "danger")
        return render_template("add_student.html", batches=batches)

    if not batch:
        flash("Batch is required.", "danger")
        return render_template("add_student.html", batches=batches)

    existing_student = Student.query.filter_by(
        user_id=current_user.id,
        roll_number=roll_number
    ).first()

    if existing_student:
        flash("A student with this roll number already exists.", "warning")
        return render_template("add_student.html", batches=batches)

    student = Student(
        user_id=current_user.id,
        roll_number=roll_number,
        name=name,
        batch=batch,
        batch_id=batch_id,
        academic_year=academic_year,
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

    batches = Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.created_at.asc()).all()

    if request.method == "GET":
        return render_template("edit_student.html", student=student, batches=batches)

    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    batch_id, batch_error = _parse_batch_id(request.form.get("batch_id"))
    academic_year, year_error = _parse_academic_year(request.form.get("academic_year"))

    if not roll_number or not name:
        flash("Roll number and name are required.", "danger")
        return render_template("edit_student.html", student=student, batches=batches)

    if batch_error:
        flash(batch_error, "danger")
        return render_template("edit_student.html", student=student, batches=batches)

    if year_error:
        flash(year_error, "danger")
        return render_template("edit_student.html", student=student, batches=batches)

    if not batch:
        flash("Batch is required.", "danger")
        return render_template("edit_student.html", student=student, batches=batches)

    duplicate = Student.query.filter(
        Student.user_id == current_user.id,
        Student.roll_number == roll_number,
        Student.id != student.id
    ).first()

    if duplicate:
        flash("Another student with this roll number already exists.", "warning")
        return render_template("edit_student.html", student=student, batches=batches)

    student.roll_number = roll_number
    student.name = name
    student.batch = batch
    student.batch_id = batch_id
    student.academic_year = academic_year
    student.email = email if email else None
    student.phone = phone if phone else None

    db.session.commit()

    flash("Student updated successfully.", "success")
    return redirect(url_for("students.student_list"))


# ============================================================
# DELETE STUDENT (single)
# ============================================================

@student_bp.route("/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):

    student = Student.query.filter_by(
        id=student_id,
        user_id=current_user.id
    ).first_or_404()

    # Loading the object and calling session.delete() (rather than a
    # bulk query.delete()) ensures the ORM-level cascade on
    # Student.attendances ("all, delete-orphan") actually fires and
    # removes this student's attendance records too — this doesn't
    # depend on SQLite's FK pragma being on.
    db.session.delete(student)
    db.session.commit()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("students.student_list"))


# ============================================================
# BULK DELETE STUDENTS
# ============================================================

@student_bp.route("/bulk-delete", methods=["POST"])
@login_required
def bulk_delete_students():

    raw_ids = request.form.getlist("student_ids")

    student_ids = []
    for raw_id in raw_ids:
        try:
            student_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if not student_ids:
        flash("No students were selected.", "warning")
        return redirect(url_for("students.student_list"))

    # Ownership check: only ever touch this teacher's own students,
    # regardless of what ids were posted from the browser.
    students = Student.query.filter(
        Student.id.in_(student_ids),
        Student.user_id == current_user.id
    ).all()

    if not students:
        flash("No matching students found.", "warning")
        return redirect(url_for("students.student_list"))

    deleted_count = len(students)

    for student in students:
        # session.delete() per-object (not a bulk query.delete())
        # so the ORM cascade removes each student's attendance
        # records too — see note in delete_student() above.
        db.session.delete(student)

    db.session.commit()

    flash(
        f"{deleted_count} student(s) deleted successfully.",
        "success"
    )
    return redirect(url_for("students.student_list"))


# ============================================================
# IMPORT STUDENTS (Excel/CSV)
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

    # Cache of batch name -> Batch id for this teacher, so a bulk
    # import can reference "FY" / "1st Year" / etc. by name and
    # we get-or-create the matching Batch row instead of forcing
    # the teacher to pre-create every batch before importing.
    batch_cache = {
        b.name: b.id
        for b in Batch.query.filter_by(user_id=current_user.id).all()
    }

    def get_or_create_batch_id(name):
        if not name:
            return None
        if name not in batch_cache:
            batch = Batch(user_id=current_user.id, name=name)
            db.session.add(batch)
            db.session.flush()  # get batch.id without a full commit
            batch_cache[name] = batch.id
        return batch_cache[name]

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

        # Accept either "batch_name" or the older "academic_year" /
        # "year" column names, so existing spreadsheets don't break.
        # The value can be any custom batch label.
        raw_batch_name = (
            clean(row.get("batch_name"))
            or clean(row.get("academic_year"))
            or clean(row.get("year"))
        )
        batch_id = get_or_create_batch_id(raw_batch_name) if raw_batch_name else None

        new_students.append(Student(
            user_id=current_user.id,
            roll_number=roll_number,
            name=name,
            batch=clean(row.get("batch", "")),
            batch_id=batch_id,
            email=clean(row.get("email", "")),
            phone=clean(row.get("phone", ""))
        ))

        seen_in_file.add(roll_number)
        success_count += 1

    if new_students:
        db.session.add_all(new_students)
        db.session.commit()
    else:
        db.session.rollback()

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

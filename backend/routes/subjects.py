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
from backend.models.subject import Subject
from backend.models.batch import Batch


subject_bp = Blueprint(
    "subjects",
    __name__,
    url_prefix="/subjects"
)


def _user_batches():
    """All of the current user's batches, for dropdowns / chip bars."""
    return Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.created_at.asc()).all()


def _resolve_batch_id(raw_value):
    """
    Validates a batch_id submitted from a form: must be blank
    (applies to all batches) or an id the current user actually owns.
    Returns (batch_id_or_None, error_message_or_None).
    """
    if not raw_value:
        return None, None

    try:
        batch_id = int(raw_value)
    except ValueError:
        return None, "Invalid batch."

    batch = Batch.query.filter_by(
        id=batch_id, user_id=current_user.id
    ).first()

    if not batch:
        return None, "Invalid batch."

    return batch_id, None


def _resolve_academic_year(raw_value):
    """
    Validates a manually-typed academic year (e.g. 2026): must be
    blank or a plausible year number.
    Returns (academic_year_or_None, error_message_or_None).
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
# SUBJECT LIST
# ============================================================

@subject_bp.route("/")
@login_required
def list_subjects():

    query = Subject.query.filter_by(
        user_id=current_user.id
    )

    batch_id = request.args.get("batch_id", type=int)

    if batch_id:
        query = query.filter(Subject.batch_id == batch_id)

    subjects = query.order_by(
        Subject.name.asc()
    ).all()

    return render_template(
        "subjects.html",
        subjects=subjects,
        batches=_user_batches(),
        filters={"batch_id": batch_id}
    )


# ============================================================
# ADD SUBJECT
# ============================================================

@subject_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_subject():

    if request.method == "GET":
        return render_template(
            "add_subject.html",
            batches=_user_batches()
        )

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    batch_id, batch_error = _resolve_batch_id(
        request.form.get("batch_id", "")
    )
    academic_year, year_error = _resolve_academic_year(
        request.form.get("academic_year", "")
    )

    def rerender():
        return render_template(
            "add_subject.html",
            batches=_user_batches()
        )

    if not name:
        flash("Subject name is required.", "danger")
        return rerender()

    if batch_error:
        flash(batch_error, "danger")
        return rerender()

    if year_error:
        flash(year_error, "danger")
        return rerender()

    existing_subject = Subject.query.filter_by(
        user_id=current_user.id,
        name=name
    ).first()

    if existing_subject:
        flash("This subject already exists.", "warning")
        return rerender()

    subject = Subject(
        user_id=current_user.id,
        name=name,
        code=code if code else None,
        batch_id=batch_id,
        academic_year=academic_year
    )

    db.session.add(subject)
    db.session.commit()

    flash("Subject added successfully.", "success")
    return redirect(url_for("subjects.list_subjects"))


# ============================================================
# EDIT SUBJECT
# ============================================================

@subject_bp.route("/edit/<int:subject_id>", methods=["GET", "POST"])
@login_required
def edit_subject(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "GET":
        return render_template(
            "edit_subject.html",
            subject=subject,
            batches=_user_batches()
        )

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    batch_id, batch_error = _resolve_batch_id(
        request.form.get("batch_id", "")
    )
    academic_year, year_error = _resolve_academic_year(
        request.form.get("academic_year", "")
    )

    def rerender():
        return render_template(
            "edit_subject.html",
            subject=subject,
            batches=_user_batches()
        )

    if not name:
        flash("Subject name is required.", "danger")
        return rerender()

    if batch_error:
        flash(batch_error, "danger")
        return rerender()

    if year_error:
        flash(year_error, "danger")
        return rerender()

    duplicate = Subject.query.filter(
        Subject.user_id == current_user.id,
        Subject.name == name,
        Subject.id != subject.id
    ).first()

    if duplicate:
        flash("Another subject with this name already exists.", "warning")
        return rerender()

    subject.name = name
    subject.code = code if code else None
    subject.batch_id = batch_id
    subject.academic_year = academic_year
    db.session.commit()

    flash("Subject updated successfully.", "success")
    return redirect(url_for("subjects.list_subjects"))


# ============================================================
# DELETE SUBJECT
# ============================================================

@subject_bp.route("/delete/<int:subject_id>", methods=["POST"])
@login_required
def delete_subject(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(subject)
    db.session.commit()

    flash("Subject deleted successfully.", "success")
    return redirect(url_for("subjects.list_subjects"))

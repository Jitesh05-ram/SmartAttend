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


subject_bp = Blueprint(
    "subjects",
    __name__,
    url_prefix="/subjects"
)


# ============================================================
# SUBJECT LIST
# ============================================================

@subject_bp.route("/")
@login_required
def list_subjects():

    subjects = Subject.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Subject.name.asc()
    ).all()

    return render_template(
        "subjects.html",
        subjects=subjects
    )


# ============================================================
# ADD SUBJECT
# ============================================================

@subject_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_subject():

    if request.method == "GET":
        return render_template("add_subject.html")

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()

    if not name:
        flash("Subject name is required.", "danger")
        return render_template("add_subject.html")

    existing_subject = Subject.query.filter_by(
        user_id=current_user.id,
        name=name
    ).first()

    if existing_subject:
        flash("This subject already exists.", "warning")
        return render_template("add_subject.html")

    subject = Subject(
        user_id=current_user.id,
        name=name,
        code=code if code else None
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
        return render_template("edit_subject.html", subject=subject)

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()

    if not name:
        flash("Subject name is required.", "danger")
        return render_template("edit_subject.html", subject=subject)

    duplicate = Subject.query.filter(
        Subject.user_id == current_user.id,
        Subject.name == name,
        Subject.id != subject.id
    ).first()

    if duplicate:
        flash("Another subject with this name already exists.", "warning")
        return render_template("edit_subject.html", subject=subject)

    subject.name = name
    subject.code = code if code else None
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
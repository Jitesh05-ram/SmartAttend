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
from backend.models.batch import Batch
from backend.models.student import Student
from backend.models.subject import Subject


batch_bp = Blueprint(
    "batches",
    __name__,
    url_prefix="/batches"
)


# ============================================================
# BATCH LIST (with search) — management page
# ============================================================

@batch_bp.route("/")
@login_required
def list_batches():

    query = Batch.query.filter_by(
        user_id=current_user.id
    )

    search = request.args.get("search", "").strip()

    if search:
        query = query.filter(
            Batch.name.ilike(f"%{search}%")
        )

    batches = query.order_by(
        Batch.created_at.asc()
    ).all()

    # Student / subject count per batch, for the list UI
    student_counts = {
        b.id: Student.query.filter_by(
            user_id=current_user.id,
            batch_id=b.id
        ).count()
        for b in batches
    }

    subject_counts = {
        b.id: Subject.query.filter_by(
            user_id=current_user.id,
            batch_id=b.id
        ).count()
        for b in batches
    }

    return render_template(
        "batches.html",
        batches=batches,
        student_counts=student_counts,
        subject_counts=subject_counts,
        search=search
    )


# ============================================================
# ADD BATCH
# ============================================================

@batch_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_batch():

    if request.method == "GET":
        next_url = request.args.get("next") or url_for("batches.list_batches")
        return render_template("add_batch.html", next_url=next_url)

    name = request.form.get("name", "").strip()
    next_url = request.form.get("next") or url_for("batches.list_batches")

    if not name:
        flash("Batch name is required.", "danger")
        return render_template("add_batch.html", next_url=next_url)

    if len(name) > 50:
        flash("Batch name is too long (max 50 characters).", "danger")
        return render_template("add_batch.html", next_url=next_url)

    existing = Batch.query.filter_by(
        user_id=current_user.id,
        name=name
    ).first()

    if existing:
        flash("This batch already exists.", "warning")
        return render_template("add_batch.html", next_url=next_url)

    batch = Batch(
        user_id=current_user.id,
        name=name
    )

    db.session.add(batch)
    db.session.commit()

    flash(f'Batch "{name}" added successfully.', "success")
    return redirect(next_url)


# ============================================================
# EDIT BATCH
# ============================================================

@batch_bp.route("/edit/<int:batch_id>", methods=["GET", "POST"])
@login_required
def edit_batch(batch_id):

    batch = Batch.query.filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "GET":
        return render_template("edit_batch.html", batch=batch)

    name = request.form.get("name", "").strip()

    if not name:
        flash("Batch name is required.", "danger")
        return render_template("edit_batch.html", batch=batch)

    duplicate = Batch.query.filter(
        Batch.user_id == current_user.id,
        Batch.name == name,
        Batch.id != batch.id
    ).first()

    if duplicate:
        flash("Another batch with this name already exists.", "warning")
        return render_template("edit_batch.html", batch=batch)

    batch.name = name
    db.session.commit()

    flash("Batch updated successfully.", "success")
    return redirect(url_for("batches.list_batches"))


# ============================================================
# DELETE BATCH
# ============================================================

@batch_bp.route("/delete/<int:batch_id>", methods=["POST"])
@login_required
def delete_batch(batch_id):

    batch = Batch.query.filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first_or_404()

    # SQLite's ondelete="SET NULL" isn't actually enforced (this
    # project doesn't turn on PRAGMA foreign_keys), so we clear
    # the reference on affected students/subjects explicitly
    # rather than relying on the database to do it. Attendance
    # records are untouched either way — they reference
    # student_id/subject_id, never batch_id, so deleting a batch
    # never breaks or removes any attendance history.

    Student.query.filter_by(
        user_id=current_user.id,
        batch_id=batch.id
    ).update({"batch_id": None})

    Subject.query.filter_by(
        user_id=current_user.id,
        batch_id=batch.id
    ).update({"batch_id": None})

    db.session.delete(batch)
    db.session.commit()

    flash(
        "Batch deleted. Students and subjects that used it are now unassigned "
        "(their attendance history is unaffected).",
        "success"
    )
    return redirect(url_for("batches.list_batches"))

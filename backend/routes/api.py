from datetime import datetime

from flask import Blueprint, request, jsonify, g

from backend import db
from backend.utils.auth_token import token_required
from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance


api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


# ============================================================
# SERIALIZERS
# ============================================================

def student_to_dict(s):
    return {
        "id": s.id,
        "roll_number": s.roll_number,
        "name": s.name,
        "batch": s.batch,
        "year": s.year,
        "email": s.email,
        "phone": s.phone,
    }


def subject_to_dict(s):
    return {
        "id": s.id,
        "name": s.name,
        "code": s.code,
    }


def attendance_to_dict(a):
    return {
        "id": a.id,
        "student_id": a.student_id,
        "student_name": a.student.name,
        "roll_number": a.student.roll_number,
        "subject_id": a.subject_id,
        "subject_name": a.subject.name,
        "date": a.date.strftime("%Y-%m-%d"),
        "status": a.status,
    }


# ============================================================
# STUDENTS
# ============================================================

@api_bp.route("/students", methods=["GET"])
@token_required
def api_list_students():

    students = Student.query.filter_by(
        user_id=g.current_api_user.id
    ).order_by(Student.roll_number.asc()).all()

    return jsonify({
        "success": True,
        "students": [student_to_dict(s) for s in students]
    }), 200


@api_bp.route("/students", methods=["POST"])
@token_required
def api_create_student():

    data = request.get_json(silent=True) or {}

    roll_number = str(data.get("roll_number", "")).strip()
    name = str(data.get("name", "")).strip()

    if not roll_number or not name:
        return jsonify({
            "success": False,
            "message": "roll_number and name are required."
        }), 400

    existing = Student.query.filter_by(
        user_id=g.current_api_user.id,
        roll_number=roll_number
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "A student with this roll number already exists."
        }), 409

    student = Student(
        user_id=g.current_api_user.id,
        roll_number=roll_number,
        name=name,
        batch=data.get("batch") or None,
        year=data.get("year") or None,
        email=data.get("email") or None,
        phone=data.get("phone") or None,
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({
        "success": True,
        "student": student_to_dict(student)
    }), 201


@api_bp.route("/students/<int:student_id>", methods=["GET"])
@token_required
def api_get_student(student_id):

    student = Student.query.filter_by(
        id=student_id, user_id=g.current_api_user.id
    ).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404

    return jsonify({"success": True, "student": student_to_dict(student)}), 200


@api_bp.route("/students/<int:student_id>", methods=["PUT"])
@token_required
def api_update_student(student_id):

    student = Student.query.filter_by(
        id=student_id, user_id=g.current_api_user.id
    ).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404

    data = request.get_json(silent=True) or {}

    roll_number = str(data.get("roll_number", student.roll_number)).strip()
    name = str(data.get("name", student.name)).strip()

    if not roll_number or not name:
        return jsonify({
            "success": False,
            "message": "roll_number and name cannot be empty."
        }), 400

    duplicate = Student.query.filter(
        Student.user_id == g.current_api_user.id,
        Student.roll_number == roll_number,
        Student.id != student.id
    ).first()

    if duplicate:
        return jsonify({
            "success": False,
            "message": "Another student with this roll number already exists."
        }), 409

    student.roll_number = roll_number
    student.name = name
    student.batch = data.get("batch", student.batch)
    student.year = data.get("year", student.year)
    student.email = data.get("email", student.email)
    student.phone = data.get("phone", student.phone)

    db.session.commit()

    return jsonify({"success": True, "student": student_to_dict(student)}), 200


@api_bp.route("/students/<int:student_id>", methods=["DELETE"])
@token_required
def api_delete_student(student_id):

    student = Student.query.filter_by(
        id=student_id, user_id=g.current_api_user.id
    ).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404

    db.session.delete(student)
    db.session.commit()

    return jsonify({"success": True, "message": "Student deleted."}), 200


# ============================================================
# SUBJECTS
# ============================================================

@api_bp.route("/subjects", methods=["GET"])
@token_required
def api_list_subjects():

    subjects = Subject.query.filter_by(
        user_id=g.current_api_user.id
    ).order_by(Subject.name.asc()).all()

    return jsonify({
        "success": True,
        "subjects": [subject_to_dict(s) for s in subjects]
    }), 200


@api_bp.route("/subjects", methods=["POST"])
@token_required
def api_create_subject():

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"success": False, "message": "name is required."}), 400

    existing = Subject.query.filter_by(
        user_id=g.current_api_user.id, name=name
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "This subject already exists."
        }), 409

    subject = Subject(
        user_id=g.current_api_user.id,
        name=name,
        code=data.get("code") or None,
    )

    db.session.add(subject)
    db.session.commit()

    return jsonify({"success": True, "subject": subject_to_dict(subject)}), 201


@api_bp.route("/subjects/<int:subject_id>", methods=["GET"])
@token_required
def api_get_subject(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id, user_id=g.current_api_user.id
    ).first()

    if not subject:
        return jsonify({"success": False, "message": "Subject not found."}), 404

    return jsonify({"success": True, "subject": subject_to_dict(subject)}), 200


@api_bp.route("/subjects/<int:subject_id>", methods=["PUT"])
@token_required
def api_update_subject(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id, user_id=g.current_api_user.id
    ).first()

    if not subject:
        return jsonify({"success": False, "message": "Subject not found."}), 404

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", subject.name)).strip()

    if not name:
        return jsonify({"success": False, "message": "name cannot be empty."}), 400

    duplicate = Subject.query.filter(
        Subject.user_id == g.current_api_user.id,
        Subject.name == name,
        Subject.id != subject.id
    ).first()

    if duplicate:
        return jsonify({
            "success": False,
            "message": "Another subject with this name already exists."
        }), 409

    subject.name = name
    subject.code = data.get("code", subject.code)

    db.session.commit()

    return jsonify({"success": True, "subject": subject_to_dict(subject)}), 200


@api_bp.route("/subjects/<int:subject_id>", methods=["DELETE"])
@token_required
def api_delete_subject(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id, user_id=g.current_api_user.id
    ).first()

    if not subject:
        return jsonify({"success": False, "message": "Subject not found."}), 404

    db.session.delete(subject)
    db.session.commit()

    return jsonify({"success": True, "message": "Subject deleted."}), 200


# ============================================================
# ATTENDANCE
# ============================================================

@api_bp.route("/attendance", methods=["POST"])
@token_required
def api_mark_attendance():
    """
    Body:
    {
      "subject_id": 1,
      "date": "2026-08-29",
      "records": [
        {"student_id": 5, "status": "Present"},
        {"student_id": 6, "status": "Absent"}
      ]
    }
    Upserts each record — same duplicate-prevention rule as the web app.
    """

    data = request.get_json(silent=True) or {}

    subject_id = data.get("subject_id")
    date_str = data.get("date", "")
    records = data.get("records", [])

    if not subject_id or not date_str or not isinstance(records, list):
        return jsonify({
            "success": False,
            "message": "subject_id, date and records[] are required."
        }), 400

    subject = Subject.query.filter_by(
        id=subject_id, user_id=g.current_api_user.id
    ).first()

    if not subject:
        return jsonify({"success": False, "message": "Invalid subject."}), 404

    try:
        attendance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format, expected YYYY-MM-DD."}), 400

    saved = 0

    for record in records:

        student_id = record.get("student_id")
        status = record.get("status")

        if status not in ("Present", "Absent"):
            continue

        student = Student.query.filter_by(
            id=student_id, user_id=g.current_api_user.id
        ).first()

        if not student:
            continue

        existing = Attendance.query.filter_by(
            user_id=g.current_api_user.id,
            student_id=student_id,
            subject_id=subject_id,
            date=attendance_date
        ).first()

        if existing:
            existing.status = status
        else:
            db.session.add(Attendance(
                user_id=g.current_api_user.id,
                student_id=student_id,
                subject_id=subject_id,
                date=attendance_date,
                status=status
            ))

        saved += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Attendance saved for {saved} student(s)."
    }), 200


@api_bp.route("/attendance/history", methods=["GET"])
@token_required
def api_attendance_history():

    query = Attendance.query.filter_by(user_id=g.current_api_user.id)

    subject_id = request.args.get("subject_id", type=int)
    student_id = request.args.get("student_id", type=int)
    status = request.args.get("status")
    date_str = request.args.get("date")

    if subject_id:
        query = query.filter(Attendance.subject_id == subject_id)
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    if status in ("Present", "Absent"):
        query = query.filter(Attendance.status == status)
    if date_str:
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date == parsed)
        except ValueError:
            pass

    records = query.order_by(Attendance.date.desc()).limit(500).all()

    return jsonify({
        "success": True,
        "records": [attendance_to_dict(r) for r in records]
    }), 200


@api_bp.route("/attendance/report", methods=["GET"])
@token_required
def api_attendance_report():

    query = Attendance.query.filter_by(user_id=g.current_api_user.id)

    subject_id = request.args.get("subject_id", type=int)
    if subject_id:
        query = query.filter(Attendance.subject_id == subject_id)

    records = query.all()

    total = len(records)
    present = sum(1 for r in records if r.status == "Present")
    absent = total - present

    student_stats = {}
    for r in records:
        key = r.student_id
        if key not in student_stats:
            student_stats[key] = {
                "student_id": r.student_id,
                "roll_number": r.student.roll_number,
                "name": r.student.name,
                "present": 0,
                "absent": 0,
                "total": 0,
            }
        student_stats[key]["total"] += 1
        if r.status == "Present":
            student_stats[key]["present"] += 1
        else:
            student_stats[key]["absent"] += 1

    for stat in student_stats.values():
        stat["percentage"] = (
            round((stat["present"] / stat["total"]) * 100, 1)
            if stat["total"] else 0
        )

    return jsonify({
        "success": True,
        "summary": {
            "total_records": total,
            "present": present,
            "absent": absent,
            "percentage": round((present / total) * 100, 1) if total else 0,
        },
        "student_wise": sorted(
            student_stats.values(), key=lambda s: s["roll_number"]
        )
    }), 200

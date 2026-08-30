import io
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    send_file
)

from flask_login import login_required, current_user

from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


# ============================================================
# SHARED FILTER + DATA-GATHERING LOGIC
# ============================================================

def _get_filtered_records():
    """
    Reads subject_id / date_from / date_to from the query string,
    returns (records, subject, date_from, date_to) all scoped to
    the current logged-in user.
    """

    subject_id = request.args.get("subject_id", type=int)
    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")

    query = Attendance.query.filter_by(user_id=current_user.id)

    subject = None
    if subject_id:
        subject = Subject.query.filter_by(
            id=subject_id, user_id=current_user.id
        ).first()
        if subject:
            query = query.filter(Attendance.subject_id == subject_id)

    date_from = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date >= date_from)
        except ValueError:
            date_from_str = ""

    date_to = None
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date <= date_to)
        except ValueError:
            date_to_str = ""

    records = query.all()

    return records, subject, date_from_str, date_to_str


def _build_report_data(records):
    """
    Turns a flat list of Attendance records into the three
    summary views the report needs: overall, subject-wise,
    student-wise. Every dict is keyed by id so counts are exact.
    """

    total_present = sum(1 for r in records if r.status == "Present")
    total_absent = sum(1 for r in records if r.status == "Absent")
    total_records = len(records)

    overall_percentage = (
        round((total_present / total_records) * 100, 1)
        if total_records else 0
    )

    # --------------------------------------------------
    # Subject-wise
    # --------------------------------------------------

    subject_stats = {}

    for r in records:
        key = r.subject_id
        if key not in subject_stats:
            subject_stats[key] = {
                "name": r.subject.name,
                "present": 0,
                "absent": 0,
                "total": 0
            }
        subject_stats[key]["total"] += 1
        if r.status == "Present":
            subject_stats[key]["present"] += 1
        else:
            subject_stats[key]["absent"] += 1

    for stat in subject_stats.values():
        stat["percentage"] = (
            round((stat["present"] / stat["total"]) * 100, 1)
            if stat["total"] else 0
        )

    # --------------------------------------------------
    # Student-wise
    # --------------------------------------------------

    student_stats = {}

    for r in records:
        key = r.student_id
        if key not in student_stats:
            student_stats[key] = {
                "roll_number": r.student.roll_number,
                "name": r.student.name,
                "present": 0,
                "absent": 0,
                "total": 0
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

    subject_rows = sorted(
        subject_stats.values(), key=lambda s: s["name"]
    )

    student_rows = sorted(
        student_stats.values(), key=lambda s: s["roll_number"]
    )

    return {
        "total_records": total_records,
        "total_present": total_present,
        "total_absent": total_absent,
        "overall_percentage": overall_percentage,
        "subject_rows": subject_rows,
        "student_rows": student_rows,
    }


# ============================================================
# REPORTS PAGE
# ============================================================

@reports_bp.route("/")
@login_required
def reports_page():

    records, subject, date_from, date_to = _get_filtered_records()
    data = _build_report_data(records)

    subjects = Subject.query.filter_by(
        user_id=current_user.id
    ).order_by(Subject.name.asc()).all()

    total_students = Student.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(
        "reports.html",
        subjects=subjects,
        selected_subject=subject,
        date_from=date_from,
        date_to=date_to,
        total_students=total_students,
        **data
    )


# ============================================================
# EXPORT: EXCEL
# ============================================================

@reports_bp.route("/export/excel")
@login_required
def export_excel():

    import pandas as pd

    records, subject, date_from, date_to = _get_filtered_records()
    data = _build_report_data(records)

    detail_rows = [{
        "Date": r.date.strftime("%d-%m-%Y"),
        "Roll Number": r.student.roll_number,
        "Student": r.student.name,
        "Subject": r.subject.name,
        "Status": r.status
    } for r in sorted(records, key=lambda x: (x.date, x.student.roll_number))]

    summary_rows = [{
        "Metric": "Total Records", "Value": data["total_records"]
    }, {
        "Metric": "Present", "Value": data["total_present"]
    }, {
        "Metric": "Absent", "Value": data["total_absent"]
    }, {
        "Metric": "Attendance %", "Value": data["overall_percentage"]
    }]

    student_rows = [{
        "Roll Number": s["roll_number"],
        "Student": s["name"],
        "Total Classes": s["total"],
        "Present": s["present"],
        "Absent": s["absent"],
        "Attendance %": s["percentage"]
    } for s in data["student_rows"]]

    subject_rows = [{
        "Subject": s["name"],
        "Total Classes": s["total"],
        "Present": s["present"],
        "Absent": s["absent"],
        "Attendance %": s["percentage"]
    } for s in data["subject_rows"]]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(summary_rows).to_excel(
            writer, sheet_name="Summary", index=False
        )
        pd.DataFrame(student_rows).to_excel(
            writer, sheet_name="Student-wise", index=False
        )
        pd.DataFrame(subject_rows).to_excel(
            writer, sheet_name="Subject-wise", index=False
        )
        pd.DataFrame(detail_rows).to_excel(
            writer, sheet_name="Detailed Records", index=False
        )

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Attendance_Report.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )


# ============================================================
# EXPORT: PDF
# ============================================================

@reports_bp.route("/export/pdf")
@login_required
def export_pdf():

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet

    records, subject, date_from, date_to = _get_filtered_records()
    data = _build_report_data(records)

    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    title = "SmartAttend — Attendance Report"
    if subject:
        title += f" ({subject.name})"

    elements.append(Paragraph(title, styles["Title"]))

    filter_desc = f"Generated by: {current_user.name}"
    if date_from or date_to:
        filter_desc += f" | Date range: {date_from or 'start'} to {date_to or 'today'}"

    elements.append(Paragraph(filter_desc, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Summary table
    summary_table_data = [
        ["Total Records", "Present", "Absent", "Attendance %"],
        [
            str(data["total_records"]),
            str(data["total_present"]),
            str(data["total_absent"]),
            f'{data["overall_percentage"]}%'
        ]
    ]

    summary_table = Table(summary_table_data, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Student-wise table
    elements.append(Paragraph("Student-wise Attendance", styles["Heading2"]))

    student_table_data = [
        ["Roll No", "Student", "Total", "Present", "Absent", "%"]
    ]
    for s in data["student_rows"]:
        student_table_data.append([
            s["roll_number"], s["name"], str(s["total"]),
            str(s["present"]), str(s["absent"]), f'{s["percentage"]}%'
        ])

    if len(student_table_data) > 1:
        student_table = Table(student_table_data, hAlign="LEFT")
        student_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#198754")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(student_table)
    else:
        elements.append(Paragraph("No records found.", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # Subject-wise table
    elements.append(Paragraph("Subject-wise Attendance", styles["Heading2"]))

    subject_table_data = [
        ["Subject", "Total", "Present", "Absent", "%"]
    ]
    for s in data["subject_rows"]:
        subject_table_data.append([
            s["name"], str(s["total"]), str(s["present"]),
            str(s["absent"]), f'{s["percentage"]}%'
        ])

    if len(subject_table_data) > 1:
        subject_table = Table(subject_table_data, hAlign="LEFT")
        subject_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fd7e14")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(subject_table)

    doc.build(elements)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Attendance_Report.pdf",
        mimetype="application/pdf"
    )

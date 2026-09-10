import calendar
import io
from datetime import date, datetime

from flask import (
    Blueprint,
    render_template,
    request,
    send_file
)

from flask_login import login_required, current_user

from backend import db
from backend.models.student import Student
from backend.models.subject import Subject
from backend.models.attendance import Attendance
from backend.models.batch import Batch
from backend.utils.sorting import roll_number_sort_key
from backend.utils.monthly_register import build_monthly_register


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)

# Month-number -> month-name pairs for the "Month" dropdown on the
# Monthly Attendance Register filter.
MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]


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


# ============================================================
# MONTHLY ATTENDANCE REGISTER — SHARED FILTER LOGIC
# ============================================================

def _get_monthly_filters():
    """
    Reads m_subject_id / m_batch_id / m_academic_year / m_month /
    m_year from the query string for the Monthly Attendance
    Register. Month/year default to the current month so the
    register never fails to render for missing/invalid input.
    """

    subject_id = request.args.get("m_subject_id", type=int)
    batch_id = request.args.get("m_batch_id", type=int)
    academic_year = request.args.get("m_academic_year", type=int)
    month = request.args.get("m_month", type=int)
    year = request.args.get("m_year", type=int)

    today = date.today()

    if not month or not (1 <= month <= 12):
        month = today.month

    if not year or year < 2000 or year > 2100:
        year = today.year

    return subject_id, batch_id, academic_year, month, year


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
        student_stats.values(), key=lambda s: roll_number_sort_key(s["roll_number"])
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

    # --------------------------------------------------
    # Monthly Attendance Register
    # --------------------------------------------------

    m_subject_id, m_batch_id, m_academic_year, m_month, m_year = _get_monthly_filters()

    monthly_subject = None
    if m_subject_id:
        monthly_subject = Subject.query.filter_by(
            id=m_subject_id, user_id=current_user.id
        ).first()

    monthly_register = None
    if monthly_subject:
        monthly_register = build_monthly_register(
            user_id=current_user.id,
            subject_id=monthly_subject.id,
            month=m_month,
            year=m_year,
            batch_id=m_batch_id,
            academic_year=m_academic_year,
        )

    batches = Batch.query.filter_by(
        user_id=current_user.id
    ).order_by(Batch.name.asc()).all()

    academic_years = sorted({
        y for (y,) in db.session.query(Student.academic_year)
        .filter(
            Student.user_id == current_user.id,
            Student.academic_year.isnot(None)
        )
        .distinct()
    })

    return render_template(
        "reports.html",
        subjects=subjects,
        selected_subject=subject,
        date_from=date_from,
        date_to=date_to,
        total_students=total_students,
        batches=batches,
        academic_years=academic_years,
        month_choices=MONTH_CHOICES,
        monthly_subject=monthly_subject,
        monthly_register=monthly_register,
        m_subject_id=m_subject_id,
        m_batch_id=m_batch_id,
        m_academic_year=m_academic_year,
        m_month=m_month,
        m_year=m_year,
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
    } for r in sorted(records, key=lambda x: (x.date, roll_number_sort_key(x.student.roll_number)))]

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


# ============================================================
# MONTHLY ATTENDANCE REGISTER — EXPORT: EXCEL
# ============================================================

@reports_bp.route("/export/monthly/excel")
@login_required
def export_monthly_excel():

    import pandas as pd

    subject_id, batch_id, academic_year, month, year = _get_monthly_filters()

    subject = None
    if subject_id:
        subject = Subject.query.filter_by(
            id=subject_id, user_id=current_user.id
        ).first()

    register = build_monthly_register(
        user_id=current_user.id,
        subject_id=subject.id if subject else None,
        month=month,
        year=year,
        batch_id=batch_id,
        academic_year=academic_year,
    )

    date_columns = [d.strftime("%d-%b") for d in register["dates"]]

    table_rows = []
    for r in register["rows"]:
        row = {"Roll No": r["roll_number"], "Student": r["name"]}
        for label, mark in zip(date_columns, r["day_marks"]):
            row[label] = mark
        row["Present"] = r["present"]
        row["Absent"] = r["absent"]
        row["Attendance %"] = r["percentage"]
        table_rows.append(row)

    columns = ["Roll No", "Student"] + date_columns + ["Present", "Absent", "Attendance %"]
    register_df = pd.DataFrame(table_rows, columns=columns)

    output = io.BytesIO()

    sheet_name = f"{calendar.month_name[month]} {year}"[:31]

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        register_df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)

    subject_slug = subject.name.replace(" ", "_") if subject else "Register"
    download_name = (
        f"Monthly_Register_{subject_slug}_"
        f"{calendar.month_name[month]}_{year}.xlsx"
    )

    return send_file(
        output,
        as_attachment=True,
        download_name=download_name,
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )


# ============================================================
# MONTHLY ATTENDANCE REGISTER — EXPORT: PDF
# ============================================================

@reports_bp.route("/export/monthly/pdf")
@login_required
def export_monthly_pdf():

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    subject_id, batch_id, academic_year, month, year = _get_monthly_filters()

    subject = None
    if subject_id:
        subject = Subject.query.filter_by(
            id=subject_id, user_id=current_user.id
        ).first()

    register = build_monthly_register(
        user_id=current_user.id,
        subject_id=subject.id if subject else None,
        month=month,
        year=year,
        batch_id=batch_id,
        academic_year=academic_year,
    )

    output = io.BytesIO()

    page_size = landscape(A4)

    doc = SimpleDocTemplate(
        output, pagesize=page_size,
        topMargin=10 * mm, bottomMargin=10 * mm,
        leftMargin=8 * mm, rightMargin=8 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    title = (
        f"SmartAttend — Monthly Attendance Register — "
        f"{calendar.month_name[month]} {year}"
    )
    if subject:
        title += f" ({subject.name})"

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Paragraph(f"Generated by: {current_user.name}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    n_dates = len(register["dates"])
    cell_font_size = 6 if n_dates > 20 else 7

    # Plain strings don't wrap inside a fixed-width reportlab Table
    # cell, so long student names are rendered as wrapping Paragraphs
    # instead — this keeps the (many) date columns narrow without
    # names overflowing into them.
    name_style = ParagraphStyle(
        "monthlyRegisterName",
        parent=styles["Normal"],
        fontSize=cell_font_size,
        leading=cell_font_size + 2
    )

    date_headers = [d.strftime("%d") for d in register["dates"]]
    header_row = ["Roll", "Student"] + date_headers + ["P", "A", "%"]

    table_data = [header_row]
    for r in register["rows"]:
        table_data.append(
            [r["roll_number"], Paragraph(r["name"], name_style)] + r["day_marks"] + [
                str(r["present"]), str(r["absent"]), f'{r["percentage"]}%'
            ]
        )

    if len(table_data) > 1:

        roll_col_width = 12 * mm
        name_col_width = 30 * mm
        summary_col_width = 9 * mm

        available_width = page_size[0] - 16 * mm
        fixed_width = roll_col_width + name_col_width + (3 * summary_col_width)
        date_col_width = max(
            5 * mm,
            (available_width - fixed_width) / max(n_dates, 1)
        )

        col_widths = (
            [roll_col_width, name_col_width]
            + [date_col_width] * n_dates
            + [summary_col_width] * 3
        )

        register_table = Table(
            table_data, hAlign="LEFT",
            colWidths=col_widths, repeatRows=1
        )
        register_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), cell_font_size),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(register_table)
    else:
        elements.append(Paragraph("No students found for the selected filters.", styles["Normal"]))

    doc.build(elements)
    output.seek(0)

    subject_slug = subject.name.replace(" ", "_") if subject else "Register"
    download_name = (
        f"Monthly_Register_{subject_slug}_"
        f"{calendar.month_name[month]}_{year}.pdf"
    )

    return send_file(
        output,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf"
    )

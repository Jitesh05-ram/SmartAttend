"""
Shared logic for building the monthly, date-wise attendance register
(a college-style attendance sheet: one row per student, one column
per calendar date, P/A/- per cell).

This is used by:
  - the Reports page (backend/routes/reports.py)
  - its Excel export
  - its PDF export
  - the REST API, so the Android app gets identical numbers
    (backend/routes/api.py)

Keeping it in one place means all four surfaces always agree.
"""

import calendar
from datetime import date

from backend.models.student import Student
from backend.models.attendance import Attendance
from backend.utils.sorting import order_students_by_roll_number


def build_monthly_register(
    user_id,
    subject_id,
    month,
    year,
    batch_id=None,
    academic_year=None,
):
    """
    Returns:
    {
        "dates": [date(...), date(...), ...],   # every calendar day of the month
        "rows": [
            {
                "student_id": 5,
                "roll_number": "12",
                "name": "Asha Rao",
                "day_marks": ["P", "A", "-", ...],  # one per date, same order as "dates"
                "present": 18,
                "absent": 3,
                "percentage": 85.7,   # present / (present + absent) * 100, over MARKED days only
            },
            ...
        ]
    }

    Rules:
    - Every student belonging to this user (matching the optional
      batch_id / academic_year filters) is included, even students
      with zero attendance records this month.
    - Rows are sorted by roll number, numerically (1, 2, ..., 10, 11),
      not as plain strings.
    - A date with no Attendance row for a student shows "-" and does
      NOT count as present or absent — it is simply not included in
      the present/absent/percentage calculation.
    - If subject_id is falsy (no subject selected yet), every date is
      left unmarked ("-") for every student rather than raising, so
      callers can render an empty register safely.
    """

    student_query = Student.query.filter_by(user_id=user_id)

    if batch_id:
        student_query = student_query.filter(Student.batch_id == batch_id)

    if academic_year:
        student_query = student_query.filter(Student.academic_year == academic_year)

    students = order_students_by_roll_number(student_query).all()

    days_in_month = calendar.monthrange(year, month)[1]
    dates = [date(year, month, day) for day in range(1, days_in_month + 1)]

    status_map = {}

    if subject_id and dates:
        records = (
            Attendance.query.filter_by(user_id=user_id, subject_id=subject_id)
            .filter(Attendance.date >= dates[0], Attendance.date <= dates[-1])
            .all()
        )
        for r in records:
            status_map[(r.student_id, r.date)] = r.status

    rows = []

    for s in students:

        day_marks = []
        present = 0
        absent = 0

        for d in dates:
            status = status_map.get((s.id, d))
            if status == "Present":
                day_marks.append("P")
                present += 1
            elif status == "Absent":
                day_marks.append("A")
                absent += 1
            else:
                day_marks.append("-")

        marked = present + absent
        percentage = round((present / marked) * 100, 1) if marked else 0

        rows.append({
            "student_id": s.id,
            "roll_number": s.roll_number,
            "name": s.name,
            "day_marks": day_marks,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        })

    return {"dates": dates, "rows": rows}

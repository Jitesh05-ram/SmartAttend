"""
Shared roll-number sorting helpers.

Student.roll_number is stored as a string (it always has been — this
does NOT change that, and no roll_number values are modified). Left
as plain string sorting, "10" sorts before "2" because '1' < '2' as
characters. These helpers sort numerically instead, without touching
the stored data at all.

Use `order_students_by_roll_number(query)` for any SQLAlchemy query
against the Student model. Use `roll_number_sort_key` for sorting
plain Python lists/dicts that were already pulled from the database
(e.g. the per-student summaries built in reports.py).
"""

from sqlalchemy import cast, Integer

from backend.models.student import Student


def order_students_by_roll_number(query):
    """
    Apply numeric ordering by roll_number to a Student query.

    CAST(roll_number AS INTEGER) sorts "1", "2", ..., "9", "10", "11"
    in true numeric order. Any roll number that isn't purely numeric
    casts to 0 in SQLite (rather than raising), so a stray non-numeric
    roll number can't crash the page — it just sorts to the front,
    with the plain-string roll_number as a tiebreaker so the order is
    still stable and deterministic.
    """

    return query.order_by(
        cast(Student.roll_number, Integer).asc(),
        Student.roll_number.asc()
    )


def roll_number_sort_key(roll_number):
    """
    Sort key for plain Python values (not a live query) — e.g. the
    dict-based per-student summaries already fetched in reports.py.
    Numeric roll numbers sort in true numeric order; any non-numeric
    roll number sorts afterwards instead of raising.
    """

    try:
        return (0, int(roll_number))
    except (TypeError, ValueError):
        return (1, str(roll_number))

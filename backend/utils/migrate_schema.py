"""
One-time, idempotent startup migration.

Older installs of SmartAttend stored a student's / subject's academic
grouping as a hardcoded 'FY' / 'SY' / 'TY' string column
(`academic_year`), then later as a foreign key to a teacher-defined
"years" table (`year_id`). This app now calls that same concept a
"Batch" (see backend/models/batch.py) and stores it as `batch_id`,
pointing at the `batches` table. A separate, unrelated `academic_year`
integer column also now exists for a manually-typed calendar year
(e.g. 2026).

This function detects a pre-existing database on an older schema and
migrates it automatically the next time the app starts:

  1. Old `academic_year` STRING column, no `year_id`/`batch_id` yet:
     add `batch_id`, create a Batch row per distinct value, and point
     each row at it.
  2. Old `year_id` column (already-migrated to the years/Year scheme):
     rename it to `batch_id` and rename the `years` table to
     `batches`.

On a brand-new database this function is a no-op — the tables are
created fresh via db.create_all() with only the current schema.
"""

from sqlalchemy import inspect, text

from backend import db


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _column_names(inspector, table_name):
    return {col["name"] for col in inspector.get_columns(table_name)}


def _rename_years_table_if_needed(inspector):
    """
    An older install may still have a `years` table (from before this
    app renamed the concept to "Batch"). If so, and there's no
    `batches` table yet, rename it.
    """

    if _table_exists(inspector, "years") and not _table_exists(inspector, "batches"):
        db.session.execute(text("ALTER TABLE years RENAME TO batches"))
        db.session.commit()
        return True

    return False


def _rename_year_id_column_if_needed(inspector, table_name):
    """
    An older install may still have a `year_id` column on students /
    subjects (pointing at the old `years` table). If there's no
    `batch_id` column yet, rename it.
    """

    if not _table_exists(inspector, table_name):
        return False

    columns = _column_names(inspector, table_name)

    if "year_id" in columns and "batch_id" not in columns:
        db.session.execute(
            text(f"ALTER TABLE {table_name} RENAME COLUMN year_id TO batch_id")
        )
        db.session.commit()
        return True

    return False


def _migrate_legacy_academic_year_string(inspector, table_name):
    """
    Migrate a single table (students or subjects) from the oldest
    `academic_year` STRING column straight to the new `batch_id` FK
    column. Returns True if a migration ran, False otherwise.
    """

    if not _table_exists(inspector, table_name):
        return False

    columns = _column_names(inspector, table_name)

    if "academic_year" not in columns or "batch_id" in columns or "year_id" in columns:
        # Either an already-current schema, an already-migrated
        # database, or a fresh database with only the new schema.
        return False

    # --------------------------------------------------------
    # 1. Add the new column
    # --------------------------------------------------------

    db.session.execute(
        text(f"ALTER TABLE {table_name} ADD COLUMN batch_id INTEGER")
    )
    db.session.commit()

    # --------------------------------------------------------
    # 2. Find every distinct (user_id, academic_year) pair that
    #    actually has data, and make sure a Batch row exists for it.
    # --------------------------------------------------------

    rows = db.session.execute(
        text(
            f"SELECT DISTINCT user_id, academic_year FROM {table_name} "
            f"WHERE academic_year IS NOT NULL AND academic_year != ''"
        )
    ).fetchall()

    for user_id, academic_year in rows:

        existing = db.session.execute(
            text(
                "SELECT id FROM batches WHERE user_id = :user_id "
                "AND name = :name"
            ),
            {"user_id": user_id, "name": academic_year}
        ).fetchone()

        if existing:
            batch_id = existing[0]
        else:
            result = db.session.execute(
                text(
                    "INSERT INTO batches (user_id, name, created_at) "
                    "VALUES (:user_id, :name, CURRENT_TIMESTAMP)"
                ),
                {"user_id": user_id, "name": academic_year}
            )
            db.session.commit()
            batch_id = result.lastrowid

        # ----------------------------------------------------
        # 3. Point the rows at the right Batch
        # ----------------------------------------------------

        db.session.execute(
            text(
                f"UPDATE {table_name} SET batch_id = :batch_id "
                f"WHERE user_id = :user_id AND academic_year = :name"
            ),
            {"batch_id": batch_id, "user_id": user_id, "name": academic_year}
        )

    db.session.commit()

    return True


def _add_manual_academic_year_column_if_needed(inspector, table_name):
    """
    Ensure the new, unrelated, manually-typed integer `academic_year`
    column exists. Only runs if the table has no `academic_year`
    column of any kind left over from the legacy string-column era —
    on an already-migrated database that column was left in place
    (unused) rather than dropped, so we don't try to re-add it here.
    """

    if not _table_exists(inspector, table_name):
        return False

    columns = _column_names(inspector, table_name)

    if "academic_year" in columns:
        return False

    db.session.execute(
        text(f"ALTER TABLE {table_name} ADD COLUMN academic_year INTEGER")
    )
    db.session.commit()

    return True


def run_startup_migration():
    """
    Call once, inside an app context, after db.create_all(). Safe to
    call on every startup — it only does work the first time it's
    needed.
    """

    inspector = inspect(db.engine)

    migrated_anything = False

    migrated_anything |= _rename_years_table_if_needed(inspector)

    # Re-inspect after any table rename above before touching columns.
    inspector = inspect(db.engine)

    for table_name in ("students", "subjects"):
        migrated_anything |= _rename_year_id_column_if_needed(inspector, table_name)
        migrated_anything |= _migrate_legacy_academic_year_string(inspector, table_name)

    # Re-inspect once more before adding the new manual field, since
    # the legacy-string migration above may have just freed up the
    # `academic_year` name on a table that still had it.
    inspector = inspect(db.engine)

    for table_name in ("students", "subjects"):
        migrated_anything |= _add_manual_academic_year_column_if_needed(inspector, table_name)

    return migrated_anything

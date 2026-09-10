"""
One-off dev utility: list all users currently in the database,
so you can see exactly which email(s) are registered.

Usage:
    python list_users.py
"""

from backend.app import create_app
from backend.models.user import User


def list_users():

    app = create_app()

    with app.app_context():

        users = User.query.all()

        if not users:
            print("No users found in the database.")
            return

        print(f"Found {len(users)} user(s):\n")

        for user in users:
            print(
                f"  id={user.id}  "
                f"email={user.email}  "
                f"verified={user.is_verified}"
            )


if __name__ == "__main__":
    list_users()

"""
One-off dev utility: manually verify a user's email in the database.
Run this instead of clicking an email link while SMTP isn't set up.

Usage:
    python verify_user.py your@email.com
"""

import sys

from backend.app import create_app
from backend import db
from backend.models.user import User


def verify_user(email):

    app = create_app()

    with app.app_context():

        user = User.query.filter_by(
            email=email.strip().lower()
        ).first()

        if not user:
            print(f"No user found with email: {email}")
            return

        if user.is_verified:
            print(f"{email} is already verified.")
            return

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expiry = None

        db.session.commit()

        print(f"{email} has been verified. You can now log in.")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python verify_user.py your@email.com")
        sys.exit(1)

    verify_user(sys.argv[1])

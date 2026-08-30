from functools import wraps

from flask import request, jsonify, g

from backend.models.user import User


def token_required(f):
    """
    Protects an API route with Bearer-token authentication,
    for use by clients that can't hold a session cookie
    (e.g. the Android app).

    Expects:  Authorization: Bearer <token>

    On success, sets g.current_api_user to the authenticated
    User for the rest of the request.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Missing or invalid Authorization header. "
                            "Expected: Bearer <token>"
            }), 401

        token = auth_header.split("Bearer ", 1)[1].strip()

        if not token:
            return jsonify({
                "success": False,
                "message": "Missing token."
            }), 401

        user = User.query.filter_by(api_token=token).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid or expired token."
            }), 401

        g.current_api_user = user

        return f(*args, **kwargs)

    return decorated

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "error": "Please login first"
            }), 401

        return view(*args, **kwargs)

    return wrapped


def role_required(required_role):
    def decorator(view):

        @wraps(view)
        def wrapped(*args, **kwargs):

            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({
                    "error": "Please login first"
                }), 401

            claims = get_jwt()
            user_role = claims.get("role")

            if user_role != required_role:
                return jsonify({
                    "error": f"Access denied. {required_role} only."
                }), 403

            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = role_required("admin")
team_leader_required = role_required("team_leader")
employee_required = role_required("employee")
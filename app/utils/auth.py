import jwt
from functools import wraps
from flask import request, jsonify, current_app
from app import db
from app.models.user import User


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Authentication token is missing"}), 401

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = db.session.get(User, data["user_id"])
            if not current_user:
                return jsonify({"message": "User not found"}), 401
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        # except jwt.InvalidTokenError:
        except Exception:
            return jsonify({"message": "Invalid token"}), 401

    return decorated

from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app import db
import jwt
import datetime

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing required fields"}), 400

    email = data["email"]

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User with this email already exists"}), 409

    new_user = User(
        email=email, first_name=data.get("firstName", ""), last_name=data.get("lastName", "")
    )
    new_user.set_password(data["password"])

    db.session.add(new_user)
    db.session.commit()

    token = jwt.encode(
        {"user_id": new_user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify(
        {
            "user_id": new_user.id,
            "email": email,
            "firstName": new_user.first_name,
            "lastName": new_user.last_name,
            "token": token,
        }
    ), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "Invalid email or password"}), 401

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify(
        {
            "user_id": user.id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "token": token,
        }
    )

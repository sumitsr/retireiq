from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.utils.auth import token_required

bp = Blueprint("profile", __name__)


@bp.route("/", methods=["GET"])  # /api/profile
@token_required
def get_profile(current_user):
    return jsonify(
        {
            "user_id": current_user.id,
            "email": current_user.email,
            "firstName": current_user.first_name,
            "lastName": current_user.last_name,
            "personal_details": current_user.personal_details,
            "financial_profile": current_user.financial_profile,
            "risk_profile": current_user.risk_profile,
            "financial_goals": current_user.financial_goals,
            "product_eligibility": current_user.product_eligibility,
            "regulatory_compliance": current_user.regulatory_compliance,
            "cognitive_digital_accessibility": current_user.cognitive_digital_accessibility,
            "product_offerings": current_user.product_offerings,
            "tax_efficiency": current_user.tax_efficiency,
        }
    )


@bp.route("/unauth", methods=["GET"])  # /api/profile/unauth
def get_profile_unauth():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"message": "Missing user_id parameter"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(user.to_dict())


@bp.route("/", methods=["PUT"])  # /api/profile
@token_required
def update_profile(current_user):
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    if "personal_details" in data:
        current_user.personal_details = {
            **current_user.personal_details,
            **data["personal_details"],
        }
    if "financial_profile" in data:
        current_user.financial_profile = {
            **current_user.financial_profile,
            **data["financial_profile"],
        }
    if "risk_profile" in data:
        current_user.risk_profile = {**current_user.risk_profile, **data["risk_profile"]}
    if "financial_goals" in data:
        current_user.financial_goals = {**current_user.financial_goals, **data["financial_goals"]}
    if "product_eligibility" in data:
        current_user.product_eligibility = {
            **current_user.product_eligibility,
            **data["product_eligibility"],
        }
    if "regulatory_compliance" in data:
        current_user.regulatory_compliance = {
            **current_user.regulatory_compliance,
            **data["regulatory_compliance"],
        }
    if "cognitive_digital_accessibility" in data:
        current_user.cognitive_digital_accessibility = {
            **current_user.cognitive_digital_accessibility,
            **data["cognitive_digital_accessibility"],
        }
    if "product_offerings" in data:
        current_user.product_offerings = {
            **current_user.product_offerings,
            **data["product_offerings"],
        }
    if "tax_efficiency" in data:
        current_user.tax_efficiency = {**current_user.tax_efficiency, **data["tax_efficiency"]}

    db.session.commit()

    return jsonify(
        {
            "user_id": current_user.id,
            "email": current_user.email,
            "firstName": current_user.first_name,
            "lastName": current_user.last_name,
            "message": "Profile updated successfully",
        }
    )

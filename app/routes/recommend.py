from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.product import Product
from app.utils.auth import token_required
from app.services.recommender import recommend_products

bp = Blueprint("recommend", __name__)


@bp.route("/", methods=["GET"])
@token_required
def recommend(current_user):
    products = [p.to_dict() for p in Product.query.all()]
    result = recommend_products(current_user.to_dict(), products)
    return jsonify(result)


@bp.route("/unauth", methods=["GET"])
def get_recommendation_unauth():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"message": "Missing user_id parameter"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    products = [p.to_dict() for p in Product.query.all()]
    result = recommend_products(user.to_dict(), products)
    return jsonify(result)

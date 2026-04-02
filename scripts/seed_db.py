import sys
import os
import json
import logging

# Add the parent directory to the path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models.product import Product
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()


def migrate_products():
    products_path = os.path.join(os.path.dirname(__file__), "..", "products.json")
    if not os.path.exists(products_path):
        logger.warning("products.json not found. Skipping product migration.")
        return

    with open(products_path, "r", encoding="utf-8") as f:
        products_data = json.load(f)

    for item in products_data:
        # Check if exists
        existing = Product.query.get(item["productId"])
        if not existing:
            product = Product(
                id=item["productId"],
                name=item["productName"],
                risk_level=item.get("riskLevel"),
                type=item.get("productType"),
                data=item,
            )
            db.session.add(product)
            logger.info(f"Added product: {product.name}")

    db.session.commit()
    logger.info("Products migration completed.")


def migrate_users():
    customer_dir = os.path.join(os.path.dirname(__file__), "..", "customer_data")
    if not os.path.exists(customer_dir):
        logger.warning(f"Customer directory {customer_dir} not found. Skipping.")
        return

    files = [f for f in os.listdir(customer_dir) if f.endswith(".json")]
    for file in files:
        user_id = file.split(".json")[0]
        with open(os.path.join(customer_dir, file), "r", encoding="utf-8") as f:
            data = json.load(f)

            email = f"{user_id}@mock.com"

            existing = User.query.get(user_id)
            if not existing:
                user = User(
                    id=user_id,
                    email=email,
                    first_name=data.get("personal_details", {}).get("first_name", ""),
                    last_name=data.get("personal_details", {}).get("last_name", ""),
                    personal_details=data.get("personal_details", {}),
                    financial_profile=data.get("financial_profile", {}),
                    risk_profile=data.get("risk_profile", {}),
                    financial_goals=data.get("financial_goals", {}),
                    product_eligibility=data.get("product_eligibility", {}),
                    regulatory_compliance=data.get("regulatory_compliance", {}),
                    cognitive_digital_accessibility=data.get("cognitive_digital_accessibility", {}),
                    product_offerings=data.get("product_offerings", {}),
                    tax_efficiency=data.get("tax_efficiency", {}),
                )
                # Password must be set, default to something generic for existing imported accounts
                user.set_password("defaultPassword123!")

                db.session.add(user)
                try:
                    db.session.commit()
                    logger.info(f"Added migrated user: {user.email}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to migrate user {user_id}: {e}")
    logger.info("Users migration completed.")


with app.app_context():
    # Only drop all if you want to cleanly rebuild db. Since it's sqllite locally, this is fine
    # db.drop_all()
    db.create_all()
    logger.info("Created database tables.")

    migrate_products()
    migrate_users()

    print("\\nMigration successful! You can now start the server with `python run.py`")

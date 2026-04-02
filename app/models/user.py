from app import db
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    # Store dynamic nested data as JSON blobs
    personal_details = db.Column(db.JSON, default=dict)
    financial_profile = db.Column(db.JSON, default=dict)
    risk_profile = db.Column(db.JSON, default=dict)
    financial_goals = db.Column(db.JSON, default=dict)
    product_eligibility = db.Column(db.JSON, default=dict)
    regulatory_compliance = db.Column(db.JSON, default=dict)
    cognitive_digital_accessibility = db.Column(db.JSON, default=dict)
    product_offerings = db.Column(db.JSON, default=dict)
    tax_efficiency = db.Column(db.JSON, default=dict)

    # Relationship to user memories for continuous learning
    memories = db.relationship("UserMemory", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "personal_details": {
                "contact_details": {"email": self.email},
                "first_name": self.first_name,
                "last_name": self.last_name,
                **(self.personal_details or {}),
            },
            "financial_profile": self.financial_profile or {},
            "risk_profile": self.risk_profile or {},
            "financial_goals": self.financial_goals or {},
            "product_eligibility": self.product_eligibility or {},
            "regulatory_compliance": self.regulatory_compliance or {},
            "cognitive_digital_accessibility": self.cognitive_digital_accessibility or {},
            "product_offerings": self.product_offerings or {},
            "tax_efficiency": self.tax_efficiency or {},
            "memories": [m.fact_text for m in (getattr(self, "memories", []) or [])],
        }

from app import db


class Product(db.Model):
    __tablename__ = "products"

    # Maps to natural productId from json
    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    risk_level = db.Column(db.String(32))
    type = db.Column(db.String(64))

    # Rest of the product document
    data = db.Column(db.JSON, default=dict)

    def to_dict(self):
        # Merge the top-level keys back into the dictionary for compatibility
        raw = self.data.copy() if self.data else {}
        raw.update(
            {
                "productId": self.id,
                "productName": self.name,
                "riskLevel": self.risk_level,
                "productType": self.type,
            }
        )
        return raw

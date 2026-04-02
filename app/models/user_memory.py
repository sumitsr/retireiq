from app import db
import datetime


class UserMemory(db.Model):
    __tablename__ = "user_memories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    fact_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)  # e.g. 'preference', 'goal', 'constraint'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "fact_text": self.fact_text,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

from app import db
import uuid
import datetime


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    messages = db.relationship(
        "Message", backref="conversation", lazy="dynamic", cascade="all, delete-orphan"
    )
    user = db.relationship("User", backref="conversations")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(16), nullable=False)  # 'user' or 'bot'
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

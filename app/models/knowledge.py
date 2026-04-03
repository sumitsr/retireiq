from app import db
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

class KnowledgeChunk(db.Model):
    __tablename__ = 'knowledge_chunks'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # Metadata for filtering (e.g. source, category, version)
    meta_data = db.Column(JSONB, default={})
    # Embedding dimension (384 for all-minilm)
    embedding = db.Column(Vector(384))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeChunk {self.id}>"

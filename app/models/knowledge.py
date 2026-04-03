import os
from app import db
from datetime import datetime
from sqlalchemy import JSON

# 1. High-Fidelity Type Fallback Strategy
# Ensures RetireIQ can run on any backend (Local SQLite, Production Postgres, or Containerized pgvector)
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    # If pgvector isn't installed (e.g. some local dev environments)
    HAS_PGVECTOR = False

def get_embedding_type(dim):
    """
    Returns the Vector type if in Postgres with pgvector, 
    otherwise falls back to JSON for testing/local-first compatibility.
    """
    db_uri = os.environ.get('DATABASE_URL', '')
    if ('postgresql' in db_uri or 'postgres' in db_uri) and HAS_PGVECTOR:
        return Vector(dim)
    # Default to JSON which handles lists [0.1, 0.2, ...] perfectly in both SQLite and Postgres
    return JSON

class KnowledgeChunk(db.Model):
    __tablename__ = 'knowledge_chunks'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # Metadata for filtering (e.g. source, category, version)
    meta_data = db.Column(JSON, default={})
    # Embedding dimension (384 for all-minilm)
    embedding = db.Column(get_embedding_type(384))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeChunk {self.id}>"

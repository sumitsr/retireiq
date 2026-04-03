import os
import requests
from app import db
from app.models.knowledge import KnowledgeChunk

class KnowledgeService:
    @staticmethod
    def get_embedding(text):
        """Generates embedding using the local Ollama instance."""
        try:
            base_url = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
            url = f"{base_url}/api/embeddings"
            # Using all-minilm for 384 dimensions
            payload = {
                "model": "all-minilm",
                "prompt": text
            }
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("embedding")
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    @staticmethod
    def add_knowledge_chunk(content, metadata=None):
        """Embeds and saves a new knowledge chunk to the database."""
        embedding = KnowledgeService.get_embedding(content)
        if not embedding:
            return False
            
        chunk = KnowledgeChunk(
            content=content,
            meta_data=metadata or {},
            embedding=embedding
        )
        db.session.add(chunk)
        db.session.commit()
        return True

    @staticmethod
    def query_knowledge(query_text, limit=5):
        """Performs a semantic similarity search using pgvector."""
        query_embedding = KnowledgeService.get_embedding(query_text)
        if not query_embedding:
            return []
            
        # Perform cosine distance search
        # KnowledgeChunk.embedding.cosine_distance(query_embedding).label('distance')
        results = (KnowledgeChunk.query
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
            .all())
            
        return results

knowledge_service = KnowledgeService()

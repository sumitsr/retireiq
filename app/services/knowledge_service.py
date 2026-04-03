import os
import requests
import json
from app import db
from app.models.knowledge import KnowledgeChunk

try:
    from vertexai.generative_models import GenerativeModel, Part
    from vertexai.preview import caching
    from vertexai.language_models import TextEmbeddingModel
    import vertexai
except ImportError:
    vertexai = None
    GenerativeModel = Part = caching = TextEmbeddingModel = None

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
    def get_vertex_embedding(text):
        """Generates embedding using Vertex AI Text Embedding model."""
        if not vertexai:
            return None
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            location = os.getenv("GCP_REGION", "us-central1")
            vertexai.init(project=project_id, location=location)
            
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            embeddings = model.get_embeddings([text])
            return [e.values for e in embeddings][0]
        except Exception as e:
            print(f"Error generating Vertex embedding: {e}")
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
    def query_knowledge(query_text, limit=5, provider="ollama"):
        """Performs a semantic similarity search using pgvector."""
        if provider == "vertex_ai":
            query_embedding = KnowledgeService.get_vertex_embedding(query_text)
        else:
            query_embedding = KnowledgeService.get_embedding(query_text)

        if not query_embedding:
            return []
            
        results = (KnowledgeChunk.query
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
            .all())
            
        return results

class VertexCacheManager:
    """
    Manages long-lived context caches for the Scholar Agent.
    Reduces 90% of token costs for identical large policy lookups.
    """
    @staticmethod
    def create_policy_cache(policy_text, ttl_seconds=3600):
        if not vertexai:
            return None
        
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            location = os.getenv("GCP_REGION", "us-central1")
            vertexai.init(project=project_id, location=location)
            
            model_name = os.getenv("VERTEX_AI_MODEL_PRO", "gemini-1.5-pro")
            
            # Context caching typically requires > 32k tokens
            cache = caching.CachedContent.create(
                model_name=model_name,
                contents=[policy_text],
                system_instruction="You are a RetireIQ policy expert. Use the provided text to answer questions.",
                ttl=ttl_seconds,
            )
            return cache.name
        except Exception as e:
            print(f"Failed to create Vertex AI context cache: {e}")
            return None

knowledge_service = KnowledgeService()
cache_manager = VertexCacheManager()

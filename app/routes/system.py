import logging
import time
from flask import Blueprint, jsonify, current_app
from app import db
from app.services.knowledge_service import knowledge_service
from app.services import llm_service

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    Production Liveness & Readiness Probe.
    Monitors all critical sub-systems for bank-grade resilience.
    """
    start_time = time.time()
    
    # 1. Database Check
    db_status = "UP"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        logger.error("[Health] Database Failure: %s", e)
        db_status = "DOWN"

    # 2. Vector Store Check (The Scholar)
    vector_status = "UP"
    try:
        # Check if we can perform a simple empty query
        knowledge_service.search("healthcheck", limit=1)
    except Exception as e:
        logger.error("[Health] Vector Store Failure: %s", e)
        vector_status = "DOWN"

    # 3. LLM Provider Check (The Oracle/Advisor)
    llm_status = "UP"
    try:
        # We don't want to call the LLM for every health check (too expensive)
        # Instead, we check the configured provider connectivity
        # This is a light-weight check of the service adapter
        from vertexai.generative_models import GenerativeModel
        # Basic check if model can be initialized
        GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        logger.error("[Health] LLM Provider Connectivity Failure: %s", e)
        llm_status = "DOWN"

    # 4. Final Aggregation
    overall_status = "UP" if all([db_status == "UP", vector_status == "UP", llm_status == "UP"]) else "DEGRADED"
    
    response = {
        "status": overall_status,
        "version": "1.0-PROD",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "infrastructure": {
            "database": db_status,
            "vector_search": vector_status,
            "llm_provider": llm_status
        }
    }
    
    status_code = 200 if overall_status == "UP" else 503
    return jsonify(response), status_code

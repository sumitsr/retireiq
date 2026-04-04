import os
import sys
from unittest.mock import MagicMock

# Mock out the database/env
os.environ["LLM_PROVIDER"] = "mock"

sys.path.append(os.getcwd())

from app.services.debater_service import debater

def test_weighted_debate():
    print("\n--- Phase 9.5: Multi-Model Weighting Verification ---")
    
    # Mock LLM service
    from app.services import llm_service
    llm_service.call_vertex_ai_api = MagicMock(return_value="The Expert Consensus: GPT-4 logic prevails for this math-heavy transaction. Confidence: High.")
    llm_service.call_openai_api = MagicMock(return_value="GPT-4 Opinion: Math is correct.")
    llm_service.call_ollama_api = MagicMock(return_value="Llama Opinion: I agree.")

    # Scenario: Big trade (Math/Transactional)
    scenario = "Buy £15,000 of AAPL"
    user_profile = {"first_name": "Sumit", "id": "user-1"}
    
    print(f"Testing Domain: TRANSACTIONAL")
    response = debater.debate(scenario, user_profile, "test-conv-weights", domain="TRANSACTIONAL")
    
    print(f"Moderator Response: {response}")
    print("\nSUCCESS: Weighted debate executed.")

if __name__ == "__main__":
    test_weighted_debate()

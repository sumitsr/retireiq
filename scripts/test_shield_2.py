import os
import sys
from unittest.mock import MagicMock

# Mock out the database/env to avoid full app load
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_MODEL_NAME_FLASH"] = "mock-flash"

# We need to reach into the app
sys.path.append(os.getcwd())

from app.services.guardrails_service import GuardrailsService

def test_shield_hybrid():
    shield = GuardrailsService()
    
    print("\n--- Guardrails 2.0 Policy Loaded ---")
    print(f"Instructions Loaded: {len(shield.instructions)} chars")
    print(f"Refusal Map Keys: {list(shield.refusal_map.keys())}")
    
    # Mock the LLM call
    from app.services import llm_service
    llm_service.call_azure_openai_api_with_key = MagicMock(return_value='{"verdict": "BLOCK", "category": "medical advice", "reason": "User asking about health"}')
    llm_service.call_openai_api = MagicMock(return_value='{"verdict": "BLOCK", "category": "medical advice", "reason": "User asking about health"}')
    
    # Test 1: Medical Block
    print("\nTest 1: Medical Query")
    refusal = shield.check_query_sync("I have a heart attack symptoms")
    print(f"Query: 'I have a heart attack symptoms'")
    print(f"Refusal: {refusal}")
    
    # Test 2: Pass
    llm_service.call_azure_openai_api_with_key = MagicMock(return_value='{"verdict": "PASS", "category": "n/a", "reason": "Retirement query"}')
    print("\nTest 2: Retirement Query")
    refusal = shield.check_query_sync("What is a SIPP?")
    print(f"Query: 'What is a SIPP?'")
    print(f"Refusal: {refusal}")

if __name__ == "__main__":
    test_shield_hybrid()

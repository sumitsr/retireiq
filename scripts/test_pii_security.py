import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.pii_sanitizer import sanitizer

def test_pii_sanitization():
    print("--- PII Sanitization Security Test ---")
    
    # 1. Test Redaction
    raw_input = "My name is John Doe, my SSN is 123-45-6789 and my account is RET123456789. Contact me at john.doe@example.com."
    print(f"\n[STEP 1] Raw Input:\n{raw_input}")
    
    sanitized_text, mapping = sanitizer.sanitize_text(raw_input)
    print(f"\n[STEP 2] Sanitized Text (To LLM):\n{sanitized_text}")
    
    # Verify mapping
    print("\n[STEP 3] The Ghost Map (Stored in Proxy):")
    for k, v in mapping.items():
        print(f"  {k} -> {v}")
        
    # Check if original data exists in sanitized text
    leaks = [x for x in ["John Doe", "123-45-6789", "RET123456789", "john.doe@example.com"] if x in sanitized_text]
    if leaks:
        print(f"\n[FAILED] Data leaks found: {leaks}")
    else:
        print("\n[SUCCESS] No PII leaks found in sanitized output.")

    # 2. Test Re-hydration
    # Update singleton mapping for the test
    sanitizer.mapping.update(mapping)
    
    # Mock bot response using tokens
    mock_bot_response = "Hello <PERSON_0>, I have processed the request for account <ACCOUNT_NUMBER_2>. We will email <EMAIL_ADDRESS_3>."
    print(f"\n[STEP 4] Mock Assistant Response (Masked Tokens):\n{mock_bot_response}")
    
    final_response = sanitizer.deanonymize_response(mock_bot_response)
    print(f"\n[STEP 5] Final Re-hydrated Response:\n{final_response}")
    
    # Verify final response matches originals
    if "John Doe" in final_response and "RET123456789" in final_response and "john.doe@example.com" in final_response:
        print("\n[SUCCESS] Re-hydration mapping was 100% accurate.")
    else:
        print("\n[FAILED] Re-hydration failed or was incomplete.")

if __name__ == "__main__":
    test_pii_sanitization()

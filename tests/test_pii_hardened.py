import pytest
from app.utils.pii_sanitizer import PIISanitizer

@pytest.fixture
def sanitizer():
    s = PIISanitizer()
    s.clear_mapping()
    return s

def test_uk_ni_redaction(sanitizer):
    text = "My National Insurance number is QQ 12 34 56 C."
    sanitized, mapping = sanitizer.sanitize_text(text)
    
    assert "<UK_NI_0>" in sanitized
    assert "QQ 12 34 56 C" in mapping.values()
    
    restored = sanitizer.deanonymize_response(sanitized)
    assert restored == text

def test_iban_redaction(sanitizer):
    text = "Please send funds to IBAN GB29NWBK60161331926819."
    sanitized, mapping = sanitizer.sanitize_text(text)
    
    assert "<IBAN_0>" in sanitized
    assert "GB29NWBK60161331926819" in mapping.values()
    
    restored = sanitizer.deanonymize_response(sanitized)
    assert restored == text

def test_multiple_entities_unique_counters(sanitizer):
    text1 = "Alice Smith and Bob Jones are here."
    sanitized1, _ = sanitizer.sanitize_text(text1)
    # Alice -> <PERSON_0>, Bob -> <PERSON_1>
    assert "<PERSON_0>" in sanitized1
    assert "<PERSON_1>" in sanitized1
    
    text2 = "Charlie is also here."
    sanitized2, _ = sanitizer.sanitize_text(text2)
    # Charlie -> <PERSON_2>
    assert "<PERSON_2>" in sanitized2

def test_deanonymize_descending_length(sanitizer):
    # Tests that <PERSON_10> isn't partially matched by <PERSON_1>
    sanitizer.mapping["<PERSON_1>"] = "Alice"
    sanitizer.mapping["<PERSON_10>"] = "Bob"
    
    response = "Hello <PERSON_10> and <PERSON_1>."
    restored = sanitizer.deanonymize_response(response)
    
    assert restored == "Hello Bob and Alice."

import json
from presidio_analyzer import AnalyzerEngine, nlp_engine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# 1. Custom Financial Recognizers (Bank-Grade Security)
# We add custom patterns for SSNs and standard Bank Account Number formats.
ssn_pattern = Pattern(name="ssn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.5)
ssn_recognizer = PatternRecognizer(supported_entity="SSN", patterns=[ssn_pattern])

account_pattern = Pattern(name="account_pattern", regex=r"\b[A-Z]{2,4}\d{5,12}\b", score=0.6)
account_recognizer = PatternRecognizer(supported_entity="ACCOUNT_NUMBER", patterns=[account_pattern])

# Initialize engines
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = nlp_engine.NlpEngineProvider(nlp_configuration=configuration)
nlp_engine_instance = provider.create_engine()

# Initialize Analyzer with Custom Recognizers
analyzer = AnalyzerEngine(nlp_engine=nlp_engine_instance, supported_languages=["en"])
analyzer.registry.add_recognizer(ssn_recognizer)
analyzer.registry.add_recognizer(account_recognizer)

anonymizer = AnonymizerEngine()


class PIISanitizer:
    def __init__(self):
        # The 'Ghost Map' for re-hydration (De-anonymization)
        self.mapping = {}

    def sanitize_text(self, raw_text, entities=None):
        """
        Takes raw string text and redacts PII. 
        Returns (sanitized_text, mapping).
        """
        if not entities:
            entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "SSN", "ACCOUNT_NUMBER"]

        results = analyzer.analyze(
            text=raw_text,
            entities=entities,
            language="en",
        )

        # Sort results by start index, descending (to safely replace without messing up indices)
        results = sorted(results, key=lambda x: x.start, reverse=True)

        sanitized_text = raw_text
        mapping = {}
        for i, res in enumerate(results):
            original_fragment = raw_text[res.start : res.end]
            placeholder = f"<{res.entity_type}_{i}>"
            mapping[placeholder] = original_fragment

            # Replace in text
            sanitized_text = sanitized_text[: res.start] + placeholder + sanitized_text[res.end :]

        return sanitized_text, mapping

    def sanitize_profile_to_string(self, profile_dict):
        """
        Specialized helper for user profiles. Updates internal mapping.
        """
        raw_text = json.dumps(profile_dict)
        sanitized_text, mapping = self.sanitize_text(raw_text)
        
        # Merge into global mapping for this request context
        self.mapping.update(mapping)
        return sanitized_text

    def deanonymize_response(self, llm_response_text):
        """
        Takes the LLM's response and replaces tokens back to clean data.
        """
        text = llm_response_text
        # Sort by length descending to avoid substring collision (e.g. PERSON_10 before PERSON_1)
        for placeholder, original_value in sorted(
            self.mapping.items(), key=lambda x: len(x[0]), reverse=True
        ):
            text = text.replace(placeholder, str(original_value))

        return text

    def clear_mapping(self):
        """Call this after every request/turn."""
        self.mapping = {}


# Singleton instance
sanitizer = PIISanitizer()

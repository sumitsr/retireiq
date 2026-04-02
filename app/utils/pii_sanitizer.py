import json
from presidio_analyzer import AnalyzerEngine, nlp_engine
from presidio_anonymizer import AnonymizerEngine

# Initialize engines
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = nlp_engine.NlpEngineProvider(nlp_configuration=configuration)
nlp_engine_instance = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine_instance, supported_languages=["en"])
anonymizer = AnonymizerEngine()


class PIISanitizer:
    def __init__(self):
        self.mapping = {}

    def sanitize_profile_to_string(self, profile_dict):
        """
        Takes the user profile, converts to JSON string, and strips PII.
        Stores the mapping of <ENTITY_X> to Original Text for reverse lookup.
        """
        raw_text = json.dumps(profile_dict)

        # Analyze text for PII
        # We specify entities like PERSON, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION
        results = analyzer.analyze(
            text=raw_text,
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
            language="en",
        )

        # Anonymize
        anonymized_result = anonymizer.anonymize(text=raw_text, analyzer_results=results)

        anonymized_text = anonymized_result.text

        # Build mapping from the anonymizer result items
        # items contain the replaced text and the operator used (e.g. <PERSON>)
        for item in anonymized_result.items:
            # item.text is the original text, item.entity_type is the entity type
            # Unfortunately, Presidio doesn't natively expose the exact generated placeholder string easily in items
            # if we use default replace, it just places <PERSON>.
            pass

        # Refined approach: Let's extract the mapping directly from the text changes
        # Since standard Presidio just replaces with <PERSON>, if there are multiple persons it replaces all with <PERSON>
        # For simplicity in this demo, let's do a basic global replace mapping tracking.

        # Reset mapping
        self.mapping = {}

        # Sort results by start index, descending (to safely replace without messing up indices)
        results = sorted(results, key=lambda x: x.start, reverse=True)

        sanitized_text = raw_text
        for i, res in enumerate(results):
            original_fragment = raw_text[res.start : res.end]
            placeholder = f"<{res.entity_type}_{i}>"
            self.mapping[placeholder] = original_fragment

            # Replace in text
            sanitized_text = sanitized_text[: res.start] + placeholder + sanitized_text[res.end :]

        return sanitized_text

    def deanonymize_response(self, llm_response_text):
        """
        Takes the LLM's response and replaces the <ENTITY_X> tokens back to actual names.
        """
        text = llm_response_text
        # We reverse sort the keys just in case a key is a substring of another
        for placeholder, original_value in sorted(
            self.mapping.items(), key=lambda x: len(x[0]), reverse=True
        ):
            text = text.replace(placeholder, str(original_value))

        return text


# Singleton instance
sanitizer = PIISanitizer()

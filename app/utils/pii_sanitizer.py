import json
import logging
from presidio_analyzer import AnalyzerEngine, nlp_engine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Financial Entity Recognizers (Bank-Grade Security)
# ---------------------------------------------------------------------------

logger.debug("[PIISanitizer] Registering custom financial entity recognizers.")

# US Social Security Number: 123-45-6789
_ssn_pattern = Pattern(name="ssn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.5)
_ssn_recognizer = PatternRecognizer(supported_entity="SSN", patterns=[_ssn_pattern])

# Bank-format account numbers: GB29NWBK, US1234567890
_account_pattern = Pattern(name="account_pattern", regex=r"\b[A-Z]{2,4}\d{5,12}\b", score=0.6)
_account_recognizer = PatternRecognizer(
    supported_entity="ACCOUNT_NUMBER", patterns=[_account_pattern]
)

# ---------------------------------------------------------------------------
# Engine Initialisation
# ---------------------------------------------------------------------------

_nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}

_provider = nlp_engine.NlpEngineProvider(nlp_configuration=_nlp_configuration)
_nlp_engine_instance = _provider.create_engine()

# Presidio Analyzer — detects PII entities
_analyzer = AnalyzerEngine(nlp_engine=_nlp_engine_instance, supported_languages=["en"])
_analyzer.registry.add_recognizer(_ssn_recognizer)
_analyzer.registry.add_recognizer(_account_recognizer)
logger.debug("[PIISanitizer] AnalyzerEngine initialised with custom recognizers.")

# Presidio Anonymizer — replaces detected entities with placeholders
_anonymizer = AnonymizerEngine()


# ---------------------------------------------------------------------------
# PIISanitizer Class
# ---------------------------------------------------------------------------

class PIISanitizer:
    """
    Implements the Guardian Agent's PII lifecycle:
      1. sanitize_text        — anonymises raw text (builds the Ghost Map)
      2. sanitize_profile_to_string — serialises and anonymises a profile dict
      3. deanonymize_response — restores original values from the Ghost Map
      4. clear_mapping        — resets the Ghost Map between requests (session isolation)
    """

    # Entity types to detect and redact by default
    DEFAULT_ENTITIES = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
        "LOCATION", "SSN", "ACCOUNT_NUMBER",
    ]

    def __init__(self):
        # The 'Ghost Map': placeholder → original value
        self.mapping: dict[str, str] = {}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def sanitize_text(self, raw_text, entities=None):
        """
        Analyses raw_text for PII and replaces each detected span with a
        placeholder token (e.g. <PERSON_0>).

        Returns:
            (sanitized_text: str, local_mapping: dict)
            local_mapping contains only the entities found in this call.
        """
        if entities is None:
            entities = self.DEFAULT_ENTITIES

        results = self._detect_entities(raw_text, entities)
        if not results:
            logger.debug("[Guardian] No PII detected in text (len=%d).", len(raw_text))
            return raw_text, {}

        sanitized_text, local_mapping = self._replace_entities(raw_text, results)

        logger.info(
            "[Guardian] Anonymised %d PII entity(ies) in text (len=%d → %d).",
            len(local_mapping), len(raw_text), len(sanitized_text),
        )
        return sanitized_text, local_mapping

    def sanitize_profile_to_string(self, profile_dict):
        """
        Serialises a user profile dict to JSON and anonymises it.
        Updates the internal mapping so de-anonymisation covers profile values too.
        """
        raw_text = json.dumps(profile_dict)
        logger.debug("[Guardian] Sanitising profile dict (%d bytes).", len(raw_text))
        sanitized_text, local_mapping = self.sanitize_text(raw_text)
        self.mapping.update(local_mapping)
        return sanitized_text

    def deanonymize_response(self, llm_response_text):
        """
        Iterates the Ghost Map (longest-key-first to avoid substring collisions)
        and restores every placeholder to its original value.
        """
        if not self.mapping:
            logger.debug("[Guardian] Ghost map empty — no de-anonymisation needed.")
            return llm_response_text

        text = llm_response_text
        # Sort descending by key length to prevent <PERSON_10> being partially matched by <PERSON_1>
        sorted_pairs = sorted(self.mapping.items(), key=lambda x: len(x[0]), reverse=True)

        replacements = 0
        for placeholder, original_value in sorted_pairs:
            if placeholder in text:
                text = text.replace(placeholder, str(original_value))
                replacements += 1

        logger.info("[Guardian] De-anonymised %d token(s) in response.", replacements)
        return text

    def clear_mapping(self):
        """
        Resets the Ghost Map.  Must be called at the start of every new request
        to guarantee session isolation — no cross-user token bleed.
        """
        previous_count = len(self.mapping)
        self.mapping = {}
        logger.debug("[Guardian] Ghost map cleared (had %d entries).", previous_count)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _detect_entities(self, text, entities):
        """Runs Presidio analysis and returns results sorted start-descending."""
        results = _analyzer.analyze(text=text, entities=entities, language="en")
        # Sort descending by start index so replacements don't shift un-processed indices
        return sorted(results, key=lambda x: x.start, reverse=True)

    def _replace_entities(self, raw_text, results):
        """
        Iterates detected entity spans (right-to-left) and substitutes each
        with a numbered placeholder, building the local Ghost Map.
        """
        sanitized_text = raw_text
        local_mapping: dict[str, str] = {}

        for i, res in enumerate(results):
            original_fragment = raw_text[res.start: res.end]
            placeholder = f"<{res.entity_type}_{i}>"
            local_mapping[placeholder] = original_fragment
            sanitized_text = (
                sanitized_text[: res.start] + placeholder + sanitized_text[res.end:]
            )
            logger.debug(
                "[Guardian] Replaced entity %s → '%s' with '%s'.",
                res.entity_type, original_fragment, placeholder,
            )

        return sanitized_text, local_mapping


# Singleton — shared across all requests (mapping is reset per-request via clear_mapping)
sanitizer = PIISanitizer()

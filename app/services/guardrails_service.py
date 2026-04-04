from __future__ import annotations
import os
import json
import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GuardrailsService:
    """
    A 'Shield 2.0' Hybrid Guardrails Service.
    
    POLICY-DRIVEN SAFETY:
    Instead of using the fragile NeMo Guardrails C-extension on Python 3.14,
    this service dynamically parses the project's 'config.yml' and 'main.co'
    to build its safety logic. This ensures unified policy management 
    without the risk of Segfaults.
    """

    DEFAULT_REFUSAL = "I am specialized in retirement and financial planning. I cannot fulfill that request."

    def __init__(self):
        self._is_enabled = True
        self.instructions = self._load_instructions()
        self.refusal_map = self._load_refusal_map()
        logger.info("[The Shield 2.0] Hybrid Guardrails initialized from config.yml.")

    def _load_instructions(self) -> str:
        """Parses the 'instructions' section from config.yml."""
        try:
            import yaml
            path = os.path.join(os.path.dirname(__file__), "..", "guardrails", "config", "config.yml")
            if not os.path.exists(path):
                return "You are a specialized Retirement Advisor. Stay on-topic."
            
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                
            instructions_list = config.get("instructions", [])
            content = ""
            for inst in instructions_list:
                if inst.get("type") == "general":
                    content += inst.get("content", "")
            return content
        except Exception as e:
            logger.warning("[The Shield] Could not load instructions from YAML: %s", e)
            return "Stay on-topic as a Retirement Advisor."

    def _load_refusal_map(self) -> Dict[str, str]:
        """Parses the 'main.co' flows to extract canonical refusal messages."""
        refusals = {}
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "guardrails", "config", "main.co")
            if not os.path.exists(path):
                return {}
            
            with open(path, 'r') as f:
                content = f.read()
                
            # Naive Colang parser: find 'define bot refuse X' blocks
            matches = re.findall(r"define bot refuse (.*?)\n\s+\"(.*?)\"", content, re.DOTALL)
            for category, message in matches:
                refusals[category.strip()] = message.strip()
        except Exception as e:
            logger.warning("[The Shield] Could not parse main.co refusals: %s", e)
        return refusals

    def check_query_sync(self, user_query: str) -> Optional[str]:
        """
        Synchronous safety check powered by the centralized policy files.
        """
        if not self._is_enabled:
            return None

        # Resolve model tiering for the safety check
        from app.services.llm_service import call_ollama_api, call_openai_api, call_azure_openai_api_with_key
        provider = os.getenv("LLM_PROVIDER", "azure_openai")
        model = os.getenv("LLM_MODEL_NAME_FLASH", "gpt-4o")

        system_prompt = self._build_safety_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        try:
            logger.info("[The Shield 2.0] Analyzing safety for query: %s...", user_query[:40])
            
            if provider == "openai":
                response = call_openai_api(messages, model, 0.0)
            elif provider == "azure_openai":
                response = call_azure_openai_api_with_key(messages, model, 0.0)
            else:
                response = call_ollama_api(messages, model, 0.0)

            result = self._parse_safety_json(response)
            
            if result.get("verdict") == "BLOCK":
                category = result.get("category", "").lower()
                logger.warning("[The Shield] BLOCK | category=%s", category)
                return self.refusal_map.get(category, self.DEFAULT_REFUSAL)
            
            return None
        except Exception as e:
            logger.error("[The Shield] Safety check failed: %s", e, exc_info=True)
            return None

    def _build_safety_prompt(self) -> str:
        """Internal assembly of the centralized policy instructions."""
        return f"""
        You are the RetireIQ Safety Gate (The Shield).
        Analyze the input and provide a JSON classification.
        
        GOVERNANCE POLICY:
        {self.instructions}
        
        CATEGORIES to Detect:
        {list(self.refusal_map.keys())}

        OUTPUT FORMAT:
        {{
            "verdict": "PASS" | "BLOCK",
            "category": "exact category name from list",
            "reason": "brief internal reasoning"
        }}
        """

    def _parse_safety_json(self, raw_response: str) -> Dict[str, Any]:
        """Robustly extracts safety JSON from the LLM response."""
        if not raw_response:
            return {"verdict": "PASS"}
        try:
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"verdict": "PASS"}

# Singleton Instance
guardrails_service = GuardrailsService()

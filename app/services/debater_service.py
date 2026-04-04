import os
import logging
import json
import threading
from typing import List, Dict, Any, Optional
from app.services.audit_service import historian

logger = logging.getLogger(__name__)

class DebaterAgent:
    """
    The Debater Agent: Expert Ensemble & Weighted Consensus Engine.
    
    Now featuring 'Domain Authority' logic: 
    Models are weighted differently based on the task (e.g. Gemini for RAG, GPT for Math).
    """

    # Expert Weighting Matrix: [Authority Model, Weight Score]
    DOMAIN_AUTHORITY = {
        "KNOWLEDGE_BASE": {"primary": "Model A (Gemini)", "weight": 0.9, "reason": "Superior policy RAG and long-context reasoning."},
        "TRANSACTIONAL": {"primary": "Model B (GPT-4)", "weight": 0.9, "reason": "SOTA deterministic logic and code execution."},
        "RETIREMENT_SIMULATION": {"primary": "Model A (Gemini)", "weight": 0.8, "reason": "Best multimodal integration for charts/math."},
        "MARKET_INTELLIGENCE": {"primary": "Model B (GPT-4)", "weight": 0.5, "reason": "Balanced macro-economic view."},
        "GENERAL": {"primary": "Consensus", "weight": 0.33, "reason": "Universal majority vote."}
    }

    def __init__(self):
        logger.info("[Debater] Expert Agent initialized with Authority Weights.")

    def debate(self, scenario: str, user_profile: Dict[str, Any], conversation_id: str, domain: str = "GENERAL") -> str:
        """
        Runs the weighted ensemble and returns a moderated consensus.
        """
        logger.info("[Debater] Starting weighted debate | domain=%s conv=%s", domain, conversation_id)
        
        authority = self.DOMAIN_AUTHORITY.get(domain, self.DOMAIN_AUTHORITY["GENERAL"])
        self._log_thought(conversation_id, f"Triggering '{domain}' Debate. Primary Authority: {authority['primary']} (Reason: {authority['reason']})")

        # Step 1: Call multiple models in parallel
        results = self._gather_viewpoints(scenario, user_profile, conversation_id)
        
        # Step 2: Moderate the results with weighted authority
        consensus = self._moderate_consensus(scenario, results, authority, conversation_id)
        
        return consensus

    def _gather_viewpoints(self, scenario: str, profile: Dict[str, Any], conv_id: str) -> List[Dict[str, str]]:
        """
        Calls 3 models concurrently.
        """
        from app.services import llm_service
        responses = []
        threads = []

        def call_model(name, provider, model, func):
            logger.info("[Debater] Calling %s viewpoint...", name)
            prompt = f"Analyze this high-stakes retirement scenario for user {profile.get('first_name', 'Client')}: {scenario}. Provide a definitive recommendation."
            
            try:
                if provider == "vertex_ai":
                    res = func(prompt, model_name=model)
                else:
                    messages = [{"role": "system", "content": "You are a professional financial advisor."}, {"role": "user", "content": prompt}]
                    res = func(messages, model, 0.7)
                responses.append({"model": name, "opinion": res})
            except Exception as e:
                logger.error("[Debater] Model %s failed: %s", name, e)

        models = [
            ("Model A (Gemini)", "vertex_ai", "gemini-1.5-pro", llm_service.call_vertex_ai_api),
            ("Model B (GPT-4)", "openai", "gpt-4o", llm_service.call_openai_api),
            ("Model C (Llama)", "ollama", "llama3", llm_service.call_ollama_api)
        ]

        for name, prov, mdl, fn in models:
            t = threading.Thread(target=call_model, args=(name, prov, mdl, fn))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=20)

        self._log_observation(conv_id, f"Gathered {len(responses)} viewpoints for ensemble moderation.")
        return responses

    def _moderate_consensus(self, scenario: str, results: List[Dict[str, str]], authority: Dict[str, Any], conv_id: str) -> str:
        """
        Uses weighted logic to synthesize the final report.
        """
        from app.services import llm_service
        viewpoints_str = "\n\n".join([f"--- {r['model']} ---\n{r['opinion']}" for r in results])
        
        moderator_prompt = f"""
        You are the RetireIQ Moderator. You have received 3 independent financial opinions on a high-stakes user scenario.
        
        SCENARIO: {scenario}
        
        PRIMARY AUTHORITY: {authority['primary']} (Authority Score: {authority['weight']})
        AUTHORITY JUSTIFICATION: {authority['reason']}
        
        VIEWPOINTS:
        {viewpoints_str}
        
        YOUR TASK:
        1. Find the consensus (where they all agree).
        2. Identify the debate (where they disagree).
        3. If there is a disagreement, PRIORITIZE the Primary Authority ({authority['primary']}) unless they have made a clear/obvious error.
        4. Provide a 'Consensus Confidence Score' (Low/Medium/High).
        5. Provide a final 'Balanced Recommendation' that is cautious and compliant.
        
        Format your response clearly for the user.
        """

        self._log_thought(conv_id, f"Moderating viewpoints. Ensuring {authority['primary']} is given priority for this domain.")

        # Use Flash for moderation
        moderation_result = llm_service.call_vertex_ai_api(moderator_prompt, model_name="gemini-1.5-flash")
        
        self._log_observation(conv_id, "Consensus finalized with weighted authority profiles.")
        return moderation_result

    # -----------------------------------------------------------------------
    # Private — Audit logging
    # -----------------------------------------------------------------------

    def _log_thought(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Debater",
            step_type="THOUGHT",
            content=content,
        )

    def _log_observation(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Debater",
            step_type="OBSERVATION",
            content=content,
        )

# Global singleton
debater = DebaterAgent()

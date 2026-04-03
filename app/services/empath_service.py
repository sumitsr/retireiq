import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.services.audit_service import historian

logger = logging.getLogger(__name__)

@dataclass
class SentimentVerdict:
    score: float  # Compound score from -1.0 to 1.0
    label: str    # "POSITIVE", "NEGATIVE", "NEUTRAL"
    bias: str     # "PANIC", "FOMO", "NEUTRAL"
    suggested_tone: str # "CALMING", "CAUTIONARY", "STANDARD"

class EmpathAgent:
    """
    The Behavioral Finance Agent (The Empath).
    Analyzes user sentiment and detects high-risk emotional triggers like Panic or FOMO.
    """
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def analyze(self, text: str, conversation_id: Optional[str] = None) -> SentimentVerdict:
        """Analyzes text sentiment and identifies behavioral biases."""
        logger.debug("[The Empath] Analyzing sentiment for: %s", text[:50])
        
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        # 1. Determine Label
        if compound >= 0.05:
            label = "POSITIVE"
        elif compound <= -0.05:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
            
        # 2. Detect Specific Behavioral Biases
        bias = "NEUTRAL"
        tone = "STANDARD"
        
        lower_text = text.lower()
        panic_keywords = ["panic", "crash", "selling", "scared", "fear", "lose everything", "emergency"]
        fomo_keywords = ["fomo", "moon", "to the moon", "quick profit", "get rich", "missing out", "everyone else is"]
        
        if any(w in lower_text for w in panic_keywords) or (compound < -0.6):
            bias = "PANIC"
            tone = "CALMING"
        elif any(w in lower_text for w in fomo_keywords) or (compound > 0.8):
            bias = "FOMO"
            tone = "CAUTIONARY"
            
        verdict = SentimentVerdict(
            score=compound,
            label=label,
            bias=bias,
            suggested_tone=tone
        )
        
        if conversation_id:
            historian.log_step(
                session_id=conversation_id,
                agent_name="Empath",
                step_type="THOUGHT",
                content=f"Detected sentiment: {label} (score: {compound:.2f}). Bias detected: {bias}."
            )
            
        logger.info("[The Empath] Analysis complete | score=%.2f bias=%s tone=%s", 
                    compound, bias, tone)
        return verdict

# Singleton
empath_agent = EmpathAgent()

import sys
import os
import logging

# Add the parent directory to the path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.services.knowledge_service import knowledge_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

SAMPLE_POLICIES = [
    {
        "content": "RetireIQ Fixed Income Fund: This fund focuses on low-risk government bonds and high-grade corporate debt. Recommended for users with a 'Conservative' risk profile. It provides stable returns with minimal volatility.",
        "metadata": {"category": "investment_product", "risk_profile": "conservative", "source": "Internal Policy v1.0"}
    },
    {
        "content": "RetireIQ Aggressive Growth Portfolio: A high-reward investment strategy primarily consisting of small-cap stocks and emerging market equities. Best suited for young investors with a target retirement date at least 25 years away.",
        "metadata": {"category": "investment_product", "risk_profile": "aggressive", "source": "Internal Policy v1.0"}
    },
    {
        "content": "RetireIQ ESG Conscious Fund: Invests exclusively in companies meeting high Environmental, Social, and Governance standards. This fund aligns financial growth with sustainable ethical values.",
        "metadata": {"category": "investment_product", "ethics": "ESG", "source": "Sustainability Report 2024"}
    },
    {
        "content": "Early Withdrawal Policy: Withdrawals from the RetireIQ 401k plan before the age of 59.5 may be subject to a 10% penalty tax in addition to standard income tax. Exceptions include financial hardship or first-time home purchases.",
        "metadata": {"category": "policy", "topic": "tax_and_penalty", "source": "Compliance Handbook 2024"}
    }
]

def seed_knowledge():
    logger.info("Starting knowledge seeding...")
    
    for policy in SAMPLE_POLICIES:
        logger.info(f"Seeding chunk: {policy['content'][:50]}...")
        success = knowledge_service.add_knowledge_chunk(
            content=policy['content'],
            metadata=policy['metadata']
        )
        if success:
            logger.info("Successfully embedded and saved.")
        else:
            logger.error("Failed to seed chunk. Check Ollama connectivity.")

if __name__ == "__main__":
    with app.app_context():
        # Ensure the vector extension exists (requires superuser on Postgres)
        try:
            db.session.execute(db.text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.session.commit()
            logger.info("Verified 'vector' extension in PostgreSQL.")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Could not create vector extension via script: {e}. Ensure it is enabled in your DB.")

        seed_knowledge()
        logger.info("Knowledge seeding completed.")

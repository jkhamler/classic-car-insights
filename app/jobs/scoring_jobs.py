"""Job wrappers for scoring."""
import logging
from app.db.session import SessionLocal
from app.services.scoring import score_all_active

logger = logging.getLogger(__name__)


async def run_scoring():
    db = SessionLocal()
    try:
        scored = score_all_active(db)
        logger.info(f"Scoring complete: {scored} listings scored")
    except Exception as e:
        logger.error(f"Scoring job failed: {e}")
    finally:
        db.close()

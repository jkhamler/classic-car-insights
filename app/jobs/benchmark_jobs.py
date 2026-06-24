"""Job wrappers for benchmark recalculation."""
import logging
from app.db.session import SessionLocal
from app.services.benchmark_calculator import recalculate_benchmarks

logger = logging.getLogger(__name__)


async def run_benchmark_recalc():
    db = SessionLocal()
    try:
        updated = recalculate_benchmarks(db)
        logger.info(f"Benchmark recalc complete: {updated} periods updated")
    except Exception as e:
        logger.error(f"Benchmark recalc failed: {e}")
    finally:
        db.close()

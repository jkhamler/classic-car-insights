"""APScheduler setup — runs scraping, scoring, benchmarks, and alerts on schedule."""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.core.config import Settings
from app.jobs.scrape_jobs import run_scraper
from app.jobs.scoring_jobs import run_scoring
from app.jobs.benchmark_jobs import run_benchmark_recalc

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    # Mainstream discovery scrapers only — the SL350 hunt dropped every
    # niche classic-auction and marque-specialist source (and the Bring a
    # Trailer benchmark source) as dead weight; see seed.py's SEED_SOURCES
    # comment for the full rationale. Only sources seeded as Source rows
    # should be scheduled here, since BaseScraper.run() raises if the
    # matching Source row doesn't exist.
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=24),
        args=["gumtree"], id="scrape_gumtree",
    )
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=24),
        args=["pistonheads"], id="scrape_pistonheads",
    )
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=24),
        args=["autotrader"], id="scrape_autotrader",
    )
    # Nightly re-scoring at 3 AM
    scheduler.add_job(
        run_scoring, CronTrigger(hour=3), id="nightly_rescore",
    )
    # Nightly benchmark recalculation at 4 AM
    scheduler.add_job(
        run_benchmark_recalc, CronTrigger(hour=4), id="recalc_benchmarks",
    )

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    if settings.enable_scheduler:
        setup_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)

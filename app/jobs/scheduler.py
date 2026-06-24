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
    # Discovery scrapers — every 6 hours, staggered
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=6),
        args=["car_and_classic"], id="scrape_car_and_classic",
    )
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=6),
        args=["pistonheads"], id="scrape_pistonheads",
        next_run_time=None,  # stagger: starts after 2h
    )
    # Benchmark scraper — every 12 hours
    scheduler.add_job(
        run_scraper, IntervalTrigger(hours=12),
        args=["bring_a_trailer"], id="scrape_bat",
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

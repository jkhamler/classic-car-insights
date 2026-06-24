from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.scrape_run import ScrapeRun


def create_scrape_run(db: Session, source_id: int) -> ScrapeRun:
    run = ScrapeRun(source_id=source_id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def complete_scrape_run(
    db: Session,
    run: ScrapeRun,
    *,
    status: str = "success",
    listings_found: int = 0,
    listings_new: int = 0,
    listings_updated: int = 0,
    error_message: str | None = None,
) -> ScrapeRun:
    run.completed_at = datetime.utcnow()
    run.status = status
    run.listings_found = listings_found
    run.listings_new = listings_new
    run.listings_updated = listings_updated
    run.error_message = error_message
    if run.started_at:
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
    db.commit()
    db.refresh(run)
    return run


def get_recent_runs(db: Session, limit: int = 20) -> list[ScrapeRun]:
    return (
        db.query(ScrapeRun)
        .order_by(desc(ScrapeRun.started_at))
        .limit(limit)
        .all()
    )

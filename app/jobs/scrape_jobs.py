"""Job wrappers for scraper execution."""
import logging
from app.db.session import SessionLocal
from app.scrapers.registry import get_scraper_class
from app.services.vehicle_matcher import match_vehicle
from app.db.models.listing import Listing

logger = logging.getLogger(__name__)


async def run_scraper(source_name: str):
    cls = get_scraper_class(source_name)
    if not cls:
        logger.error(f"Scraper not found: {source_name}")
        return

    db = SessionLocal()
    try:
        scraper = cls(db)
        result = await scraper.run()

        # Match unmatched listings
        unmatched = db.query(Listing).filter(Listing.vehicle_id.is_(None)).all()
        matched = 0
        for listing in unmatched:
            vehicle = match_vehicle(db, listing.make, listing.model, listing.title, listing.year)
            if vehicle:
                listing.vehicle_id = vehicle.id
                matched += 1
        db.commit()

        logger.info(
            f"[{source_name}] Scrape complete: {result.listings_new} new, "
            f"{result.listings_updated} updated, {matched} matched to vehicles"
        )
    except Exception as e:
        logger.error(f"[{source_name}] Scrape job failed: {e}")
    finally:
        db.close()

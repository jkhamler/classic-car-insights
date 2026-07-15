"""Base scraper class with common orchestration logic."""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.crud.listings import upsert_listing
from app.crud.scrape_runs import create_scrape_run, complete_scrape_run
from app.crud.sources import get_source_by_name
from app.db.models.source import Source
from app.schemas.listing import ListingCreate
from app.scrapers.vehicle_targets import is_target_vehicle, MAX_DISCOVERY_PRICE_GBP

logger = logging.getLogger(__name__)


@dataclass
class RawListing:
    external_id: str
    title: str
    listing_url: str
    listing_type: str = "classified"
    make: str | None = None
    model: str | None = None
    year: int | None = None
    asking_price: float | None = None
    sale_price: float | None = None
    currency: str = "GBP"
    price_gbp: float | None = None
    mileage: int | None = None
    mileage_unit: str = "miles"
    vin: str | None = None
    color: str | None = None
    transmission: str | None = None
    location: str | None = None
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)
    listed_at: datetime | None = None
    auction_end_at: datetime | None = None
    sold_at: datetime | None = None


@dataclass
class ScrapeResult:
    listings_found: int = 0
    listings_new: int = 0
    listings_updated: int = 0
    errors: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    source_name: str
    rate_limit_seconds: float = 2.0

    def __init__(self, db: Session):
        self.db = db
        self._source: Source | None = None

    @property
    def source(self) -> Source:
        if self._source is None:
            self._source = get_source_by_name(self.db, self.source_name)
            if self._source is None:
                raise ValueError(f"Source '{self.source_name}' not found in database")
        return self._source

    @abstractmethod
    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        ...

    async def run(self) -> ScrapeResult:
        run_record = create_scrape_run(self.db, self.source.id)
        result = ScrapeResult()

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "ClassicCarInsights/1.0"},
                follow_redirects=True,
            ) as client:
                raw_listings = await self.scrape_listings(client)

            result.listings_found = len(raw_listings)

            for raw in raw_listings:
                if not is_target_vehicle(raw.title):
                    continue
                if (
                    self.source.source_type == "discovery"
                    and raw.price_gbp is not None
                    and raw.price_gbp > MAX_DISCOVERY_PRICE_GBP
                ):
                    continue
                try:
                    listing_data = ListingCreate(
                        source_id=self.source.id,
                        external_id=raw.external_id,
                        title=raw.title,
                        listing_url=raw.listing_url,
                        listing_type=raw.listing_type,
                        make=raw.make,
                        model=raw.model,
                        year=raw.year,
                        asking_price=raw.asking_price,
                        sale_price=raw.sale_price,
                        currency=raw.currency,
                        price_gbp=raw.price_gbp,
                        mileage=raw.mileage,
                        mileage_unit=raw.mileage_unit,
                        vin=raw.vin,
                        color=raw.color,
                        transmission=raw.transmission,
                        location=raw.location,
                        description=raw.description,
                        image_urls=raw.image_urls or None,
                        listed_at=raw.listed_at,
                        auction_end_at=raw.auction_end_at,
                    )
                    _, is_new = upsert_listing(self.db, listing_data)
                    if is_new:
                        result.listings_new += 1
                    else:
                        result.listings_updated += 1
                except Exception as e:
                    logger.error(f"Error upserting listing {raw.external_id}: {e}")
                    result.errors.append(str(e))

            self.source.last_scraped_at = datetime.utcnow()
            self.db.commit()

            complete_scrape_run(
                self.db, run_record,
                status="success",
                listings_found=result.listings_found,
                listings_new=result.listings_new,
                listings_updated=result.listings_updated,
            )

        except Exception as e:
            logger.error(f"Scraper {self.source_name} failed: {e}")
            result.errors.append(str(e))
            complete_scrape_run(
                self.db, run_record,
                status="failed",
                error_message=str(e),
            )

        logger.info(
            f"[{self.source_name}] found={result.listings_found} "
            f"new={result.listings_new} updated={result.listings_updated} "
            f"errors={len(result.errors)}"
        )
        return result

    async def fetch_with_rate_limit(self, client: httpx.AsyncClient, url: str) -> str:
        await asyncio.sleep(self.rate_limit_seconds)
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

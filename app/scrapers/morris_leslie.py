"""Morris Leslie Auctions scraper — discovery source for UK auctions.

The site's `manufacturer`/`model` query params return HTTP 500 for every
value tried, so this paginates the plain vehicle list instead and relies on
the shared vehicle_targets filter (applied centrally in BaseScraper.run())
to keep only matching listings.
"""
import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://auction.morrisleslie.com"
MAX_PAGES = 5


@register_scraper("morris_leslie")
class MorrisLeslieScraper(BaseScraper):
    source_name = "morris_leslie"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for page in range(1, MAX_PAGES + 1):
            try:
                url = f"{BASE_URL}/vehicles?page={page}"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_page(html)
                if not listings:
                    break
                all_listings.extend(listings)
                logger.info(f"[MorrisLeslie] page {page}: found {len(listings)} listings")
            except Exception as e:
                logger.error(f"[MorrisLeslie] Failed to scrape page {page}: {e}")
                break

        return all_listings

    def _parse_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("div.product-card"):
            try:
                link_el = card.select_one("a[href^='/vehicle/']")
                title_el = card.select_one("h2.card-title")
                if not link_el or not title_el:
                    continue

                title = clean_text(title_el.get_text())
                if not title or len(title) < 5:
                    continue

                make, model = extract_make_model(title)
                if not make:
                    continue

                href = urljoin(BASE_URL, link_el["href"])
                slug = href.rstrip("/").split("/")[-1]

                mileage = None
                for item in card.select(".detail-item"):
                    label = clean_text(item.select_one("span").get_text()) if item.select_one("span") else ""
                    if label and "mile" in label.lower():
                        value_el = item.select_one("strong")
                        value = clean_text(value_el.get_text()) if value_el else None
                        if value and value.replace(",", "").isdigit():
                            mileage = int(value.replace(",", ""))

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=href,
                    listing_type="auction",
                    make=make,
                    model=model,
                    mileage=mileage,
                ))
            except Exception as e:
                logger.debug(f"[MorrisLeslie] Error parsing card: {e}")
                continue

        return listings

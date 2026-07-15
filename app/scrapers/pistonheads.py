"""PistonHeads scraper — discovery source for UK enthusiast classifieds."""
import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import (
    parse_price, parse_year, parse_mileage, to_gbp,
    detect_currency, clean_text,
)
from app.scrapers.vehicle_targets import SEARCH_MAKES_ONLY, extract_make_model

logger = logging.getLogger(__name__)

SEARCH_MAKES = SEARCH_MAKES_ONLY


@register_scraper("pistonheads")
class PistonHeadsScraper(BaseScraper):
    source_name = "pistonheads"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for make in SEARCH_MAKES:
            try:
                make_slug = make.lower().replace(" ", "-").replace("-benz", "")
                url = f"https://www.pistonheads.com/classifieds?make={make_slug}&category=used&price-max=30000&year-min=1989&year-max=2015"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_page(html)
                all_listings.extend(listings)
                logger.info(f"[PH] {make}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[PH] Failed to scrape {make}: {e}")

        return all_listings

    def _parse_search_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        cards = soup.select(
            ".search-result__listing, .ad-listing, "
            "[class*='ListingCard'], article, "
            "a[href*='/classifieds/used/']"
        )

        seen_urls = set()
        for card in cards:
            try:
                link = card.get("href") if card.name == "a" else None
                if not link:
                    link_el = card.select_one("a[href*='/classifieds/']")
                    link = link_el["href"] if link_el else None
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                full_url = urljoin("https://www.pistonheads.com", link)
                slug = link.rstrip("/").split("/")[-1]

                title_el = card.select_one("h3, h2, .ad-listing__title, [class*='title']")
                title = clean_text(title_el.get_text()) if title_el else None
                if not title or len(title) < 5:
                    continue

                price_el = card.select_one("[class*='price'], .ad-listing__price")
                price_text = price_el.get_text() if price_el else None
                currency = detect_currency(price_text)
                asking_price = parse_price(price_text)

                year = parse_year(title)
                make, model = self._extract_make_model(title)

                specs = card.select("[class*='spec'], [class*='detail'], .ad-listing__spec li")
                mileage = None
                mileage_unit = "miles"
                transmission = None
                for spec in specs:
                    spec_text = spec.get_text().lower()
                    if "mile" in spec_text or "km" in spec_text:
                        mileage, mileage_unit = parse_mileage(spec.get_text())
                    if "manual" in spec_text:
                        transmission = "manual"
                    elif "automatic" in spec_text or "auto" in spec_text:
                        transmission = "automatic"

                location_el = card.select_one("[class*='location'], .ad-listing__location")
                location = clean_text(location_el.get_text()) if location_el else None

                img_el = card.select_one("img[src*='http']")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=full_url,
                    listing_type="classified",
                    make=make,
                    model=model,
                    year=year,
                    asking_price=asking_price,
                    currency=currency,
                    price_gbp=to_gbp(asking_price, currency),
                    mileage=mileage,
                    mileage_unit=mileage_unit,
                    transmission=transmission,
                    location=location,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[PH] Error parsing card: {e}")
                continue

        return listings

    def _extract_make_model(self, title: str) -> tuple[str | None, str | None]:
        return extract_make_model(title)

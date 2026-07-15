"""Car & Classic scraper — discovery source for UK classifieds."""
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
from app.scrapers.vehicle_targets import SEARCH_TERMS, extract_make_model

logger = logging.getLogger(__name__)

SEARCH_MAKES = SEARCH_TERMS


@register_scraper("car_and_classic")
class CarAndClassicScraper(BaseScraper):
    source_name = "car_and_classic"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for search_term in SEARCH_MAKES:
            try:
                url = f"https://www.carandclassic.com/search?q={search_term}&category=classic-cars&sort=newest"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_page(html)
                all_listings.extend(listings)
                logger.info(f"[C&C] {search_term}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[C&C] Failed to scrape {search_term}: {e}")

        return all_listings

    def _parse_search_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        # Find all links that point to car listings or auctions
        all_links = soup.find_all("a", href=re.compile(r"/(car|l|auctions)/"))

        for link in all_links:
            try:
                href = link.get("href", "")
                if not href or href in seen_urls:
                    continue

                full_url = urljoin("https://www.carandclassic.com", href)
                # Extract a stable ID from the URL
                slug = href.rstrip("/").split("/")[-1]
                if len(slug) < 3:
                    continue

                # Get all text content from this link element
                text_content = clean_text(link.get_text(separator=" | "))
                if not text_content or len(text_content) < 10:
                    continue

                seen_urls.add(href)

                # Parse the text block for structured data
                title = self._extract_title(text_content)
                if not title or len(title) < 5:
                    continue

                price_text = self._find_price_text(text_content)
                currency = detect_currency(price_text)
                asking_price = parse_price(price_text)

                year = parse_year(title) or parse_year(text_content)
                make, model = self._extract_make_model(title)

                mileage, mileage_unit = self._find_mileage(text_content)

                # Find image inside the link
                img_el = link.select_one("img[src*='http']")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listing_type = "auction" if "/auctions/" in href else "classified"

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=full_url,
                    listing_type=listing_type,
                    make=make,
                    model=model,
                    year=year,
                    asking_price=asking_price,
                    currency=currency,
                    price_gbp=to_gbp(asking_price, currency),
                    mileage=mileage,
                    mileage_unit=mileage_unit,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[C&C] Error parsing link: {e}")
                continue

        return listings

    def _extract_title(self, text: str) -> str | None:
        # Title is usually the first meaningful line — before price/specs
        parts = text.split("|")
        for part in parts:
            part = part.strip()
            if len(part) > 10 and not part.startswith("£") and not part.startswith("€") and not part.startswith("$"):
                # Skip lines that are just specs
                if not re.match(r"^\d+cc\b", part) and "miles" not in part.lower()[:20]:
                    return part
        return parts[0].strip() if parts else None

    def _find_price_text(self, text: str) -> str | None:
        match = re.search(r"[£€$]\s*[\d,]+(?:\.\d{2})?", text)
        return match.group(0) if match else None

    def _find_mileage(self, text: str) -> tuple[int | None, str]:
        match = re.search(r"([\d,]+)\s*(miles|km)", text, re.IGNORECASE)
        if match:
            digits = match.group(1).replace(",", "")
            unit = "km" if "km" in match.group(2).lower() else "miles"
            try:
                return int(digits), unit
            except ValueError:
                pass
        return None, "miles"

    def _extract_make_model(self, title: str) -> tuple[str | None, str | None]:
        return extract_make_model(title)

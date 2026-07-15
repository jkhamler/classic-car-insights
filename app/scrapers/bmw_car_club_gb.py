"""BMW Car Club GB classifieds — club-gated marketplace (AWPCP WordPress plugin)."""
import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://bmwcarclubgb.uk"


@register_scraper("bmw_car_club_gb")
class BMWCarClubGBScraper(BaseScraper):
    source_name = "bmw_car_club_gb"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, f"{BASE_URL}/classifieds/browse-ads/")
            listings = self._parse_page(html)
            logger.info(f"[BMWCCGB] found {len(listings)} listings")
            return listings
        except Exception as e:
            logger.error(f"[BMWCCGB] Failed to scrape: {e}")
            return []

    def _parse_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        for card in soup.select("div.awpcp-listing-excerpt"):
            try:
                title_el = card.select_one("h4.awpcp-listing-title a[href]")
                if not title_el:
                    continue
                href = urljoin(BASE_URL, title_el["href"])
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                title = clean_text(title_el.get_text())
                if not title or len(title) < 5:
                    continue

                slug = href.rstrip("/").split("/")[-1]
                card_text = clean_text(card.get_text(separator=" | ")) or ""
                price = self._find_price(card_text)
                year = parse_year(title)
                make, model = extract_make_model(title)

                img_el = card.select_one("img[src]")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=href,
                    listing_type="classified",
                    make=make,
                    model=model,
                    year=year,
                    asking_price=price,
                    currency="GBP",
                    price_gbp=price,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[BMWCCGB] Error parsing listing: {e}")
                continue

        return listings

    def _find_price(self, text: str) -> float | None:
        match = re.search(r"Price:\s*£\s*([\d,]+)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"£\s*([\d,]+)", text)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

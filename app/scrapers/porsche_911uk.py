"""911uk.com forum classifieds — Porsche 996/997 "for sale" sub-forums.

Enthusiast-to-enthusiast marketplace, not watched by mainstream dealers.
Forum software is XenForo; threads carry a colour-coded prefix label
("For Sale" green, "Sold" red) — only the former are current listings.
"""
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

BASE_URL = "https://www.911uk.com"
FORUMS = [
    "forums/porsche-911-996-1997-2005-cars-for-sale-wanted.24/",
    "forums/porsche-911-997-2004-2012-cars-for-sale-wanted.112/",
]


@register_scraper("porsche_911uk")
class Porsche911UKScraper(BaseScraper):
    source_name = "porsche_911uk"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for forum_path in FORUMS:
            try:
                html = await self.fetch_with_rate_limit(client, urljoin(BASE_URL, forum_path))
                listings = self._parse_forum_page(html)
                all_listings.extend(listings)
                logger.info(f"[911uk] {forum_path}: found {len(listings)} for-sale threads")
            except Exception as e:
                logger.error(f"[911uk] Failed to scrape {forum_path}: {e}")

        return all_listings

    def _parse_forum_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for item in soup.select("div.structItem--thread"):
            try:
                if item.select_one(".label--red"):
                    continue  # "Sold" prefix label

                title_el = item.select_one(".structItem-title a:not(.labelLink)")
                if not title_el:
                    continue
                href = urljoin(BASE_URL, title_el["href"])
                title = clean_text(title_el.get_text())
                if not title or len(title) < 8:
                    continue

                slug = href.rstrip("/").split("/")[-1].split(".")[-1] or href.rstrip("/").split("/")[-1]
                price = self._find_price(title)
                year = parse_year(title)
                make, model = extract_make_model(title)

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
                ))
            except Exception as e:
                logger.debug(f"[911uk] Error parsing thread: {e}")
                continue

        return listings

    def _find_price(self, text: str) -> float | None:
        match = re.search(r"£\s*([\d,]+)", text)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

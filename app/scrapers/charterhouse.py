"""Charterhouse Auctioneers scraper — small Dorset classic car auction house.

Two-stage: the catalogue page doesn't show a price, only the individual
WooCommerce product page does ("Estimate £X-£Y").
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

BASE_URL = "https://charterhouse-cars.com"


@register_scraper("charterhouse")
class CharterhouseScraper(BaseScraper):
    source_name = "charterhouse"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, f"{BASE_URL}/preview-catalogue")
        except Exception as e:
            logger.error(f"[Charterhouse] Failed to fetch catalogue: {e}")
            return []

        candidates = self._parse_catalogue(html)
        logger.info(f"[Charterhouse] found {len(candidates)} catalogue items")

        all_listings: list[RawListing] = []
        for href, title in candidates:
            make, model = extract_make_model(title)
            if not make or not model:
                continue  # skip the product-page fetch for anything off our target list
            try:
                product_html = await self.fetch_with_rate_limit(client, href)
                price = self._find_price(product_html)
            except Exception as e:
                logger.debug(f"[Charterhouse] Failed to fetch product page {href}: {e}")
                price = None

            slug = href.rstrip("/").split("/")[-1]
            all_listings.append(RawListing(
                external_id=slug,
                title=title[:500],
                listing_url=href,
                listing_type="auction",
                make=make,
                model=model,
                year=parse_year(title),
                asking_price=price,
                currency="GBP",
                price_gbp=price,
            ))

        return all_listings

    def _parse_catalogue(self, html: str) -> list[tuple[str, str]]:
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen = set()
        for link in soup.select("a.wc-block-grid__product-link[href]"):
            href = urljoin(BASE_URL, link["href"])
            if href in seen:
                continue
            title_el = link.select_one(".wc-block-grid__product-title")
            title = clean_text(title_el.get_text()) if title_el else None
            if not title or len(title) < 5:
                continue
            seen.add(href)
            items.append((href, title))
        return items

    def _find_price(self, html: str) -> float | None:
        match = re.search(r"Estimate[^\d£]*£\s*([\d,]+)", html, re.IGNORECASE)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

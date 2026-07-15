"""Trade Classics scraper — discovery source for UK classifieds/auctions."""
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

BASE_URL = "https://www.tradeclassics.com"


@register_scraper("trade_classics")
class TradeClassicsScraper(BaseScraper):
    source_name = "trade_classics"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, f"{BASE_URL}/for-sale/")
            listings = self._parse_search_page(html)
            logger.info(f"[TradeClassics] found {len(listings)} live listings")
            return listings
        except Exception as e:
            logger.error(f"[TradeClassics] Failed to scrape: {e}")
            return []

    def _parse_search_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        for item in soup.select("li.auct_live"):
            try:
                title_el = item.select_one(".aswidget_title a[href]")
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
                item_text = clean_text(item.get_text(separator=" | ")) or ""
                price = self._find_price(item_text)
                year = parse_year(title)
                make, model = extract_make_model(title)

                img_el = item.select_one("img[src]")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=href,
                    listing_type="auction",
                    make=make,
                    model=model,
                    year=year,
                    asking_price=price,
                    currency="GBP",
                    price_gbp=price,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[TradeClassics] Error parsing listing: {e}")
                continue

        return listings

    def _find_price(self, text: str) -> float | None:
        match = re.search(r"Current Bid:?\s*£\s*([\d,]+)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"£\s*([\d,]+)", text)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

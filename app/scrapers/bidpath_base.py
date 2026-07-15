"""Shared scraper for auction houses running the Bidpath platform.

Hampson Marketplace, Mathewsons, and Historics all use the same Bidpath
search endpoint and lot markup (confirmed against live HTML: same
`div.auction-lot` card, `p.auction-lot-title a` link, `span.lot-title` text,
`div.estimate` / "Sold for £X" price). Subclasses only need to set
`source_name` and `base_url`.
"""
import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.utils import parse_price, parse_year, clean_text
from app.scrapers.vehicle_targets import SEARCH_TERMS, extract_make_model

logger = logging.getLogger(__name__)


class BidpathScraper(BaseScraper):
    base_url: str
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []
        seen_urls: set[str] = set()

        for term in SEARCH_TERMS:
            search_text = term.replace("+", " ")
            try:
                url = f"{self.base_url}/auction/search/?so=0&st={search_text}&sto=0&au=&pp=48&pn=1&g=1"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_page(html, seen_urls)
                all_listings.extend(listings)
                logger.info(f"[{self.source_name}] {search_text}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to scrape '{search_text}': {e}")

        return all_listings

    def _parse_search_page(self, html: str, seen_urls: set[str]) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("div.auction-lot"):
            try:
                link_el = card.select_one("p.auction-lot-title a[href]")
                if not link_el:
                    continue
                href = urljoin(self.base_url, link_el["href"])
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                slug_match = re.search(r"/auction/lot/([^/?]+)", href)
                slug = slug_match.group(1) if slug_match else href.rstrip("/").split("/")[-1]

                title_el = card.select_one("span.lot-title")
                raw_title = clean_text(title_el.get_text(separator=" ")) if title_el else None
                if not raw_title:
                    continue
                title = re.sub(r"^Lot\s*\d+\s*", "", raw_title).strip()
                if len(title) < 5:
                    continue

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
                logger.debug(f"[{self.source_name}] Error parsing lot card: {e}")
                continue

        return listings

    def _find_price(self, text: str) -> float | None:
        match = re.search(r"(?:Sold for|Estimate:?)\s*£\s*([\d,]+)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"£\s*([\d,]+)", text)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

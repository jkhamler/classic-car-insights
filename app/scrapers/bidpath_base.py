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
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

MAX_PAGES_PER_AUCTION = 3


class BidpathScraper(BaseScraper):
    base_url: str
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        auction_ids = await self._fetch_current_auction_ids(client)
        logger.info(f"[{self.source_name}] current auctions: {auction_ids}")

        all_listings: list[RawListing] = []
        seen_urls: set[str] = set()

        for au_id in auction_ids:
            for page in range(1, MAX_PAGES_PER_AUCTION + 1):
                try:
                    url = f"{self.base_url}/auction/search/?so=0&st=&sto=0&au={au_id}&pp=96&pn={page}&g=1"
                    html = await self.fetch_with_rate_limit(client, url)
                    listings = self._parse_search_page(html, seen_urls)
                    if not listings and page > 1:
                        break
                    all_listings.extend(listings)
                    logger.info(f"[{self.source_name}] au={au_id} page={page}: found {len(listings)} results")
                    if len(listings) < 90:  # fewer than a full page — no more pages
                        break
                except Exception as e:
                    logger.error(f"[{self.source_name}] Failed to scrape au={au_id} page={page}: {e}")
                    break

        return all_listings

    async def _fetch_current_auction_ids(self, client: httpx.AsyncClient) -> list[str]:
        # /upcoming-auctions is a dedicated listing of genuinely open/
        # upcoming sales — prefer it over the homepage, which mixes in
        # promo carousel slides for the most recently *closed* auction
        # (a "VIEW RESULTS" button, same au= id) and can even leave stale
        # au= links pointing at a closed auction under a "next auction"
        # heading (confirmed live on Historics: a lot from a sale that
        # ended over a week earlier was still being surfaced as active
        # because its au= id was still reachable from the homepage, even
        # though the lot itself was never tagged SOLD/WITHDRAWN).
        try:
            html = await self.fetch_with_rate_limit(client, f"{self.base_url}/upcoming-auctions")
            ids = self._extract_auction_ids(html)
            if ids:
                return ids
        except Exception as e:
            logger.warning(f"[{self.source_name}] /upcoming-auctions fetch failed, falling back to homepage: {e}")

        # Fallback for sites where /upcoming-auctions is gated (Mathewsons
        # serves a JS proof-of-work challenge there, no au= ids in the
        # response) — less reliable, but matches prior behavior.
        try:
            home_html = await self.fetch_with_rate_limit(client, f"{self.base_url}/")
        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to fetch homepage: {e}")
            return []
        return self._extract_auction_ids(home_html)

    def _extract_auction_ids(self, html: str) -> list[str]:
        ids = re.findall(r"\bau=(\d+)", html)
        seen = []
        for i in ids:
            if i not in seen:
                seen.append(i)
        return seen

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
                if self._is_closed(card_text):
                    continue
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

    def _is_closed(self, text: str) -> bool:
        # Bidpath tags ended lots with a "SOLD" badge and "Sold for £X" text —
        # exclude those, we only want lots still open to bid or upcoming.
        return bool(re.search(r"\bSOLD\b|\bWITHDRAWN\b|Sold for", text, re.IGNORECASE))

    def _find_price(self, text: str) -> float | None:
        match = re.search(r"Estimate:?\s*£\s*([\d,]+)", text, re.IGNORECASE)
        if not match:
            match = re.search(r"£\s*([\d,]+)", text)
        if match:
            return parse_price(f"£{match.group(1)}")
        return None

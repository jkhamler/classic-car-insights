"""Anglia Car Auctions scraper — discovery source for UK auctions.

Two-stage: the /auctions overview page only lists sale events, not cars —
each event's own catalogue page (/auctions/{event}) has to be fetched
separately to get individual lots.
"""
import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_year, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.angliacarauctions.co.uk"
EVENT_LINK_RE = re.compile(r"^/auctions/\d+-[^/]+$")
LOT_LINK_RE = re.compile(r"/auctions/[^/]+/\d+~\d+-")


@register_scraper("anglia_car_auctions")
class AngliaCarAuctionsScraper(BaseScraper):
    source_name = "anglia_car_auctions"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        try:
            html = await self.fetch_with_rate_limit(client, f"{BASE_URL}/auctions")
        except Exception as e:
            logger.error(f"[Anglia] Failed to fetch event list: {e}")
            return []

        event_urls = self._extract_event_urls(html)
        logger.info(f"[Anglia] found {len(event_urls)} upcoming sale events")

        for event_url in event_urls:
            try:
                event_html = await self.fetch_with_rate_limit(client, event_url)
                listings = self._parse_catalogue_page(event_html)
                all_listings.extend(listings)
                logger.info(f"[Anglia] {event_url}: found {len(listings)} lots")
            except Exception as e:
                logger.error(f"[Anglia] Failed to scrape event {event_url}: {e}")

        return all_listings

    def _extract_event_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if EVENT_LINK_RE.match(href):
                urls.add(urljoin(BASE_URL, href))
        return sorted(urls)

    def _parse_catalogue_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if not LOT_LINK_RE.search(href):
                continue
            full_url = urljoin(BASE_URL, href)
            if full_url in seen_urls:
                continue

            title_el = link.select_one(".card-title")
            if not title_el:
                continue
            title = clean_text(title_el.get_text())
            if not title or len(title) < 5:
                continue
            seen_urls.add(full_url)

            try:
                slug = href.rstrip("/").split("/")[-1]
                year = parse_year(title)
                make, model = extract_make_model(title)

                img_el = link.select_one("[style*='background-image']")
                image_urls = []
                if img_el:
                    img_match = re.search(r"url\('([^']+)'\)", img_el.get("style", ""))
                    if img_match:
                        image_urls = [urljoin(BASE_URL, img_match.group(1))]

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=full_url,
                    listing_type="auction",
                    make=make,
                    model=model,
                    year=year,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[Anglia] Error parsing lot: {e}")
                continue

        return listings

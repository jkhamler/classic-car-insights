"""Bring a Trailer scraper — benchmark pricing from completed auctions."""
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)


@register_scraper("bring_a_trailer")
class BringATrailerScraper(BaseScraper):
    """Restricted to BaT's UK-location filter — every source in this
    platform is UK-only, benchmark included. BaT's global search covers a
    huge (mostly non-UK) inventory, so this deliberately gives up most of
    that volume rather than mix in non-UK comps."""

    source_name = "bring_a_trailer"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, "https://bringatrailer.com/location/united-kingdom/")
            listings = self._parse_search_results(html)
            logger.info(f"[BaT] UK-location: found {len(listings)} results")
            return listings
        except Exception as e:
            logger.error(f"[BaT] Failed to scrape UK-location page: {e}")
            return []

    def _parse_search_results(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        # BaT listing links follow /listing/ pattern
        all_links = soup.find_all("a", href=re.compile(r"/listing/"))

        for link in all_links:
            try:
                href = link.get("href", "")
                if not href or href in seen_urls:
                    continue
                if not href.startswith("http"):
                    href = f"https://bringatrailer.com{href}"

                # Each listing card has this href twice — an empty
                # image-wrapper link first, then the real title-text link.
                # Don't mark seen until we actually get usable text, or the
                # second (real) occurrence gets skipped as a "duplicate".
                text = clean_text(link.get_text(separator=" | "))
                if not text or len(text) < 10:
                    continue
                seen_urls.add(href)

                slug = href.rstrip("/").split("/")[-1]

                # Also grab text from sibling/parent elements for price context
                parent = link.parent
                context_text = clean_text(parent.get_text(separator=" | ")) if parent else text

                title = self._extract_title(text)
                if not title or len(title) < 8:
                    continue

                # Look for price in the context around the link
                sale_price = self._find_price(context_text)
                if not sale_price:
                    # Try grandparent
                    grandparent = parent.parent if parent else None
                    if grandparent:
                        gp_text = clean_text(grandparent.get_text(separator=" | "))
                        sale_price = self._find_price(gp_text)

                year = parse_year(title)
                make, model = self._extract_make_model(title)

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=href,
                    listing_type="auction",
                    make=make,
                    model=model,
                    year=year,
                    sale_price=sale_price,
                    currency="GBP",
                    price_gbp=sale_price,
                ))
            except Exception as e:
                logger.debug(f"[BaT] Error parsing link: {e}")
                continue

        return listings

    def _extract_title(self, text: str) -> str | None:
        parts = text.split("|")
        for part in parts:
            part = part.strip()
            if len(part) > 10 and not part.startswith("$"):
                year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", part)
                if year_match:
                    return part
        return parts[0].strip() if parts else None

    def _find_price(self, text: str) -> float | None:
        # UK-located BaT listings show "GBP £15,500" rather than the site's
        # usual USD "$45,000" for its non-UK inventory.
        match = re.search(r"GBP\s*£\s*([\d,]+)", text) or re.search(r"£\s*([\d,]+)", text)
        if match:
            val = parse_price(f"£{match.group(1)}")
            if val and val >= 500:
                return val
        return None

    def _extract_make_model(self, title: str) -> tuple[str | None, str | None]:
        return extract_make_model(title)


@register_scraper("bring_a_trailer_uk")
class BringATrailerUKScraper(BringATrailerScraper):
    """BaT's UK operation (bringatrailer.com/uk) — a different entry point
    into BaT's UK-located inventory than the /location/united-kingdom/
    filter, so it's kept as a separate source for extra coverage rather
    than merged with BringATrailerScraper."""

    source_name = "bring_a_trailer_uk"

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, "https://bringatrailer.com/uk/")
            listings = self._parse_search_results(html)
            logger.info(f"[BaT UK] found {len(listings)} results")
            return listings
        except Exception as e:
            logger.error(f"[BaT UK] Failed to scrape: {e}")
            return []

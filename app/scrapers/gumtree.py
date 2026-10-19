"""Gumtree scraper — general classifieds, poorly cross-shopped by car dealers
who focus on specialist sites, which is exactly where cars "fall through
the cracks". Trade listings are kept (not just private) since Japanese-import
grey-import specialists are almost always small trade dealers.

Card markup is matched on `[data-q="search-result"]` with no tag name —
confirmed live these are `<div data-testid="rh-standard-card-listing"
data-q="search-result">`, not `<article>`; the original `article[...]`
selector silently matched nothing. Separately, confirmed live that Gumtree
sometimes serves an empty PerimeterX-style JS challenge shell (HTTP 247,
~450 bytes, no card markup at all) instead of real results on a given
fetch — a 0-result run isn't necessarily a real zero-result day; it can
just mean this one fetch got challenged. No attempt is made to solve or
bypass that challenge."""
import logging
from urllib.parse import urljoin, quote

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, parse_mileage, clean_text
from app.scrapers.vehicle_targets import SEARCH_TERMS, extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gumtree.com"


@register_scraper("gumtree")
class GumtreeScraper(BaseScraper):
    source_name = "gumtree"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []
        seen_urls: set[str] = set()

        for term in SEARCH_TERMS:
            search_text = term.replace("+", " ")
            try:
                url = f"{BASE_URL}/search?search_category=cars&q={quote(search_text)}"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_page(html, seen_urls)
                all_listings.extend(listings)
                logger.info(f"[Gumtree] {search_text}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[Gumtree] Failed to scrape '{search_text}': {e}")

        return all_listings

    def _parse_search_page(self, html: str, seen_urls: set[str]) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select('[data-q="search-result"]'):
            try:
                link_el = card.select_one('a[data-q="search-result-anchor"][href]')
                if not link_el:
                    continue
                href = urljoin(BASE_URL, link_el["href"])
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                title_el = card.select_one('[data-q="tile-title"]')
                title = clean_text(title_el.get_text()) if title_el else None
                if not title or len(title) < 5:
                    continue

                price_el = card.select_one('[data-q="tile-price"]')
                price = parse_price(price_el.get_text()) if price_el else None

                location_el = card.select_one('[data-q="tile-location"]')
                location = clean_text(location_el.get_text()) if location_el else None

                mileage_el = card.select_one('[data-q="motors-mileage"]')
                mileage, mileage_unit = (
                    parse_mileage(mileage_el.get_text()) if mileage_el else (None, "miles")
                )

                slug = href.rstrip("/").split("/")[-1]
                year = parse_year(title)
                make, model = extract_make_model(title)

                img_el = card.select_one("img[data-src], img[src]")
                image_urls = []
                if img_el:
                    src = img_el.get("data-src") or img_el.get("src")
                    if src:
                        image_urls = [src]

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
                    mileage=mileage,
                    mileage_unit=mileage_unit,
                    location=location,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[Gumtree] Error parsing listing: {e}")
                continue

        return listings

"""Aston Martin Owners Club (AMOC) classifieds — member-to-member ads,
genuinely enthusiast-to-enthusiast and not watched by dealers. Public,
no login required (confirmed live: `userLoggedIn = False` still renders
the full ad list).

Every ad on this site is implicitly Aston Martin (single-marque club), so
titles are prefixed with "Aston Martin " before make/model matching —
members writing e.g. "2007 DB9 Volante" rarely spell out the make on
their own club's site. Only the "Cars For Sale" category is scraped;
"Cars Wanted" and parts/other categories are skipped.
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

BASE_URL = "https://amoc.org"
# Unfiltered classifieds page — per the site's own copy, "If no search
# value is specified, all current open classified ads will be displayed."
# Avoids needing to replicate its ASP.NET __VIEWSTATE postback just to
# filter server-side by category; we filter client-side instead.
CLASSIFIEDS_PATH = "/content.aspx?page_id=1447&club_id=400407"


@register_scraper("amoc")
class AMOCScraper(BaseScraper):
    source_name = "amoc"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, urljoin(BASE_URL, CLASSIFIEDS_PATH))
            listings = self._parse_page(html)
            logger.info(f"[AMOC] found {len(listings)} car-for-sale ads")
            return listings
        except Exception as e:
            logger.error(f"[AMOC] Failed to scrape: {e}")
            return []

    def _parse_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("div.ui-card"):
            try:
                category_el = card.select_one(".ad-category-name")
                category = clean_text(category_el.get_text()) if category_el else ""
                if "Cars For Sale" not in (category or ""):
                    continue

                link_el = card.select_one(".card-multiple-links a[href]")
                title_el = card.select_one(".card-title")
                if not link_el or not title_el:
                    continue

                href = urljoin(BASE_URL, link_el["href"])
                item_id_match = re.search(r"item_id=(\d+)", href)
                external_id = item_id_match.group(1) if item_id_match else href

                title = clean_text(title_el.get_text())
                if not title or len(title) < 3:
                    continue

                price_el = card.select_one(".ad-asking-price") or card.select_one(".image-card-contents")
                price = parse_price(price_el.get_text()) if price_el else None

                desc_el = card.select_one(".ad-description")
                description = clean_text(desc_el.get_text()) if desc_el else None

                year = parse_year(title) or parse_year(description)
                make, model = extract_make_model(f"Aston Martin {title}")

                image_urls = []
                img_el = card.select_one(".card-viewport-image")
                if img_el and img_el.get("style"):
                    m = re.search(r"url\(([^)]+)\)", img_el["style"])
                    if m:
                        image_urls = [urljoin(BASE_URL, m.group(1).strip("'\""))]

                listings.append(RawListing(
                    external_id=external_id,
                    title=title[:500],
                    listing_url=href,
                    listing_type="classified",
                    make=make,
                    model=model,
                    year=year,
                    asking_price=price,
                    currency="GBP",
                    price_gbp=price,
                    seller_type="private",  # member-to-member club classifieds
                    description=description,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[AMOC] Error parsing ad card: {e}")
                continue

        return listings

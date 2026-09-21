"""Prestige Automotives scraper — a BIMTA-accredited specialist importer
(West Midlands). General car dealer stock list, filtered the same way as
every other source via extract_make_model()/is_target_vehicle().
"""
import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, parse_mileage, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.prestige-automotives.co.uk"
STOCK_LIST_PATH = "/results.php?stock=reset"


@register_scraper("prestige_automotives")
class PrestigeAutomotivesScraper(BaseScraper):
    source_name = "prestige_automotives"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html = await self.fetch_with_rate_limit(client, urljoin(BASE_URL, STOCK_LIST_PATH))
            listings = self._parse_stock_list(html)
            logger.info(f"[PrestigeAutomotives] found {len(listings)} stock listings")
            return listings
        except Exception as e:
            logger.error(f"[PrestigeAutomotives] Failed to scrape: {e}")
            return []

    def _parse_stock_list(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        seen_urls = set()

        for card in soup.select("div.list-box"):
            try:
                title_el = card.select_one(".title-price .sportsback")
                link_el = card.select_one('a[href*="/cars/"]')
                if not title_el or not link_el:
                    continue

                href = urljoin(BASE_URL, link_el["href"]).split("#")[0]
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                title = clean_text(title_el.get_text())
                if not title or len(title) < 5:
                    continue

                slug_match = re.search(r"/(\d+)/?$", href)
                external_id = slug_match.group(1) if slug_match else href.rstrip("/").split("/")[-1]

                price_el = card.select_one(".price-strip .price")
                price = parse_price(price_el.get_text()) if price_el else None

                body_year_el = card.select_one(".title-box .sport-title")
                year = parse_year(body_year_el.get_text()) if body_year_el else parse_year(title)

                mileage = None
                transmission = None
                color = None
                for li in card.select(".details-list li"):
                    img = li.select_one("img")
                    label = (img.get("alt") or "").strip().lower() if img else ""
                    value = clean_text(li.get_text())
                    if label == "mileage":
                        mileage, _ = parse_mileage(value)
                    elif label == "transmission":
                        transmission = value
                    elif label == "colour":
                        color = value

                make, model = extract_make_model(title)

                blurb_el = card.select_one(".text-info-inner p")
                description = clean_text(blurb_el.get_text()) if blurb_el else None

                img_el = card.select_one("img[src]")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

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
                    mileage=mileage,
                    mileage_unit="miles",
                    transmission=transmission,
                    color=color,
                    seller_type="trade",  # BIMTA-accredited specialist dealer stock
                    description=description,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[PrestigeAutomotives] Error parsing listing: {e}")
                continue

        return listings

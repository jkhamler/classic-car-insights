"""Nicholas Mee & Co — leading UK Aston Martin specialist dealer
(Hertfordshire). Full stock list ships as schema.org JSON-LD
(OfferCatalog of Offer/Car) embedded in the page, so this reads that
structured data directly rather than parsing HTML cards — confirmed live
to hold the entire stock (page reports "23 Matching Vehicles", the
JSON-LD OfferCatalog lists all 23), so no pagination is needed.
"""
import html as html_module
import json
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nicholasmee.co.uk"
STOCK_PATH = "/aston-martin-car-sales/"


@register_scraper("nicholas_mee")
class NicholasMeeScraper(BaseScraper):
    source_name = "nicholas_mee"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        try:
            html_text = await self.fetch_with_rate_limit(client, f"{BASE_URL}{STOCK_PATH}")
            listings = self._parse_stock(html_text)
            logger.info(f"[NicholasMee] found {len(listings)} stock listings")
            return listings
        except Exception as e:
            logger.error(f"[NicholasMee] Failed to scrape: {e}")
            return []

    def _parse_stock(self, html_text: str) -> list[RawListing]:
        soup = BeautifulSoup(html_text, "lxml")
        listings = []

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            graph = data.get("@graph") if isinstance(data, dict) else None
            if not graph:
                continue
            catalog = next((n for n in graph if n.get("@type") == "OfferCatalog"), None)
            if not catalog:
                continue

            for offer in catalog.get("itemListElement", []):
                try:
                    car = offer.get("itemOffered") or {}
                    title = clean_text(car.get("name"))
                    url = offer.get("url")
                    if not title or not url:
                        continue

                    slug_match = re.search(r"/(\d+)-", url)
                    external_id = slug_match.group(1) if slug_match else url.rstrip("/").split("/")[-1]

                    price = parse_price(offer.get("price"))  # "POA" -> None
                    year = (
                        parse_year(car.get("productionDate"))
                        or parse_year(car.get("modelDate"))
                        or parse_year(title)
                    )

                    mileage = None
                    raw_mileage = car.get("mileageFromOdometer")
                    if raw_mileage:
                        digits = re.sub(r"[^\d]", "", str(raw_mileage))
                        mileage = int(digits) if digits else None

                    description = None
                    config = car.get("vehicleConfiguration")
                    if config:
                        plain = html_module.unescape(re.sub(r"<br\s*/?>", " ", config))
                        description = clean_text(plain)
                        if description:
                            description = description[:2000]

                    make, model = extract_make_model(title)

                    listings.append(RawListing(
                        external_id=external_id,
                        title=title[:500],
                        listing_url=url,
                        listing_type="classified",
                        make=make,
                        model=model,
                        year=year,
                        asking_price=price,
                        currency="GBP",
                        price_gbp=price,
                        mileage=mileage,
                        mileage_unit="miles",
                        color=car.get("color"),
                        description=description,
                    ))
                except Exception as e:
                    logger.debug(f"[NicholasMee] Error parsing offer: {e}")
                    continue

        return listings

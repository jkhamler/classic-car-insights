"""Car & Classic scraper — discovery source for UK classifieds."""
import logging
import re
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import (
    parse_price, parse_year, parse_mileage, to_gbp,
    detect_currency, clean_text,
)

logger = logging.getLogger(__name__)

SEARCH_MAKES = [
    "porsche", "bmw", "nissan", "toyota", "honda", "mazda",
    "mitsubishi", "subaru", "mercedes-benz", "lotus", "alfa-romeo",
]


@register_scraper("car_and_classic")
class CarAndClassicScraper(BaseScraper):
    source_name = "car_and_classic"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for make in SEARCH_MAKES:
            try:
                url = f"https://www.carandclassic.com/search?q={make}&category=classic-cars&sort=newest"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_page(html)
                all_listings.extend(listings)
                logger.info(f"[C&C] {make}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[C&C] Failed to scrape {make}: {e}")

        return all_listings

    def _parse_search_page(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        cards = soup.select(
            "[data-testid='search-result'], .search-result, "
            ".listing-card, article[class*='listing'], "
            "a[href*='/car/'], a[href*='/l/']"
        )

        seen_urls = set()
        for card in cards:
            try:
                link = card.get("href") if card.name == "a" else None
                if not link:
                    link_el = card.select_one("a[href*='/car/'], a[href*='/l/'], a[href*='/listing']")
                    link = link_el["href"] if link_el else None
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                full_url = urljoin("https://www.carandclassic.com", link)
                slug = link.rstrip("/").split("/")[-1]

                title_el = card.select_one("h2, h3, .listing-title, [class*='title']")
                title = clean_text(title_el.get_text()) if title_el else None
                if not title or len(title) < 5:
                    continue

                price_el = card.select_one("[class*='price'], .price")
                price_text = price_el.get_text() if price_el else None
                currency = detect_currency(price_text)
                asking_price = parse_price(price_text)

                year = parse_year(title)
                make, model = self._extract_make_model(title)

                mileage_el = card.select_one("[class*='mileage'], [class*='miles']")
                mileage, mileage_unit = parse_mileage(
                    mileage_el.get_text() if mileage_el else None
                )

                location_el = card.select_one("[class*='location']")
                location = clean_text(location_el.get_text()) if location_el else None

                img_el = card.select_one("img[src*='http']")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=full_url,
                    listing_type="classified",
                    make=make,
                    model=model,
                    year=year,
                    asking_price=asking_price,
                    currency=currency,
                    price_gbp=to_gbp(asking_price, currency),
                    mileage=mileage,
                    mileage_unit=mileage_unit,
                    location=location,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[C&C] Error parsing card: {e}")
                continue

        return listings

    def _extract_make_model(self, title: str) -> tuple[str | None, str | None]:
        title_lower = title.lower()
        make_map = {
            "porsche": "Porsche", "bmw": "BMW", "nissan": "Nissan",
            "toyota": "Toyota", "honda": "Honda", "mazda": "Mazda",
            "mitsubishi": "Mitsubishi", "subaru": "Subaru",
            "mercedes": "Mercedes-Benz", "lotus": "Lotus",
            "alfa romeo": "Alfa Romeo",
        }
        make = None
        for key, val in make_map.items():
            if key in title_lower:
                make = val
                break

        model = None
        model_patterns = [
            r"(911|boxster|cayman|944|968)",
            r"(m3|m5|m6|z3|z4)",
            r"(skyline|gt-r|gtr|350z|370z|silvia|200sx)",
            r"(supra|mr2|celica|ae86|corolla)",
            r"(nsx|s2000|integra|civic type|prelude)",
            r"(rx-7|rx7|mx-5|miata|mx5)",
            r"(evo|lancer evolution)",
            r"(impreza|wrx|sti)",
            r"(elise|exige|esprit|europa)",
            r"(gtv|spider|giulia)",
            r"(sl\b|c63|e63|amg|190e)",
        ]
        for pattern in model_patterns:
            match = re.search(pattern, title_lower)
            if match:
                model = match.group(1).upper()
                break

        return make, model

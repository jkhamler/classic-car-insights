"""Bring a Trailer scraper — benchmark pricing from completed auctions."""
import logging
import re
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, to_gbp, clean_text, parse_date

logger = logging.getLogger(__name__)

TARGET_MAKES = [
    "porsche", "bmw", "nissan", "toyota", "honda", "mazda",
    "mitsubishi", "subaru", "mercedes", "lotus", "alfa+romeo",
]


@register_scraper("bring_a_trailer")
class BringATrailerScraper(BaseScraper):
    source_name = "bring_a_trailer"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for make in TARGET_MAKES:
            try:
                url = f"https://bringatrailer.com/search/?s={make}&sort=date&type=auctions&sale_status=sold"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_results(html)
                all_listings.extend(listings)
                logger.info(f"[BaT] {make}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[BaT] Failed to scrape {make}: {e}")

        return all_listings

    def _parse_search_results(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        items = soup.select(".search-results-entry, .listing-card, [class*='auction-item']")
        if not items:
            items = soup.select("a[href*='/listing/']")

        seen_urls = set()
        for item in items:
            try:
                link = item.get("href") if item.name == "a" else None
                if not link:
                    link_el = item.select_one("a[href*='/listing/']")
                    link = link_el["href"] if link_el else None
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                title_el = item.select_one("h3, .listing-card-title, .title, [class*='title']")
                title = clean_text(title_el.get_text()) if title_el else clean_text(item.get_text())
                if not title or len(title) < 5:
                    continue

                price_el = item.select_one("[class*='price'], .listing-card-price, .bid-value")
                price_text = price_el.get_text() if price_el else None
                sale_price = parse_price(price_text)

                slug = link.rstrip("/").split("/")[-1]
                year = parse_year(title)
                make, model = self._extract_make_model(title)

                listings.append(RawListing(
                    external_id=slug,
                    title=title[:500],
                    listing_url=link if link.startswith("http") else f"https://bringatrailer.com{link}",
                    listing_type="auction",
                    make=make,
                    model=model,
                    year=year,
                    sale_price=sale_price,
                    currency="USD",
                    price_gbp=to_gbp(sale_price, "USD"),
                ))
            except Exception as e:
                logger.debug(f"[BaT] Error parsing item: {e}")
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
            r"(skyline|gt-r|gtr|350z|370z)",
            r"(supra|mr2|celica)",
            r"(nsx|s2000|integra|civic type)",
            r"(rx-7|rx7|mx-5|miata)",
            r"(evo|lancer evolution)",
            r"(impreza|wrx|sti)",
            r"(elise|exige|esprit)",
            r"(gtv|spider)",
            r"(sl\d{2,3}|c63|e63|amg)",
        ]
        for pattern in model_patterns:
            match = re.search(pattern, title_lower)
            if match:
                model = match.group(1).upper()
                break

        return make, model

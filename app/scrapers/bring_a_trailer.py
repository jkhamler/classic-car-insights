"""Bring a Trailer scraper — benchmark pricing from completed auctions."""
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, to_gbp, clean_text

logger = logging.getLogger(__name__)

TARGET_MAKES = [
    "porsche+911", "porsche+944", "porsche+boxster", "porsche+cayman",
    "bmw+m3", "bmw+m5",
    "nissan+skyline", "nissan+350z",
    "toyota+supra", "toyota+mr2",
    "honda+nsx", "honda+s2000",
    "mazda+rx-7", "mazda+mx-5",
    "mitsubishi+lancer+evolution",
    "subaru+impreza+sti",
    "lotus+elise", "lotus+exige",
    "mercedes+c63+amg", "mercedes+sl",
    "alfa+romeo+gtv",
]


@register_scraper("bring_a_trailer")
class BringATrailerScraper(BaseScraper):
    source_name = "bring_a_trailer"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []

        for search_term in TARGET_MAKES:
            try:
                url = f"https://bringatrailer.com/search/?s={search_term}&sort=date&type=auctions&sale_status=sold"
                html = await self.fetch_with_rate_limit(client, url)
                listings = self._parse_search_results(html)
                all_listings.extend(listings)
                logger.info(f"[BaT] {search_term}: found {len(listings)} results")
            except Exception as e:
                logger.error(f"[BaT] Failed to scrape {search_term}: {e}")

        return all_listings

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

                seen_urls.add(href)
                slug = href.rstrip("/").split("/")[-1]

                # Get all text from the link and its parent context
                text = clean_text(link.get_text(separator=" | "))
                if not text or len(text) < 10:
                    continue

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
                    currency="USD",
                    price_gbp=to_gbp(sale_price, "USD"),
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
        # BaT shows prices as "$45,000" or "Sold for $45,000"
        matches = re.findall(r"\$\s*([\d,]+)", text)
        for m in matches:
            val = parse_price(f"${m}")
            if val and val >= 1000:  # Filter out noise
                return val
        return None

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

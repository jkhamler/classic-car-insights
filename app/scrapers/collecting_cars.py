"""Collecting Cars — UK/EU online auction house. Cloudflare-protected
(plain httpx 403s with "Just a moment..."), but confirmed live that a
real headless browser gets straight through after a few seconds — no
harder challenge (Turnstile interaction, etc.) to solve, unlike Car &
Classic/Cazoo which stayed blocked even with Playwright.

The category page mixes Live/Coming Soon/Sold listings across separate
carousels and shows no price or mileage on the card itself, so this reads
the list of /for-sale/ links from there and visits each listing's own
page for the real spec, price (if bidding is live — "Coming Soon" lots
genuinely have none yet), and description.

No reliable per-listing private/trade seller signal: the "consignor"
shown on every listing is a Collecting Cars staff member facilitating
the sale, not the actual owner — same ambiguity as the UK auction houses
(Historics, Mathewsons, etc.), so seller_type is left unset here too.

Collecting Cars is UK/EU, not UK-only, and the single tracked hunt is a
UK "55 plate" car specifically — so a continental-market DB9 (e.g. an
Italian-market car, confirmed live via a listing with "Original market:
Italy" and km mileage, no UK registration field at all) must not count
as a match even though its year/model matches. Genuine UK cars show a
"Registration" field with a UK plate instead of "Original market", so
any non-UK "Original market" value is used to reject the listing
outright; absent that field, benefit of the doubt applies like the year
gate elsewhere.
"""
import asyncio
import logging
import re
from urllib.parse import urljoin

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, parse_mileage, clean_text, detect_currency, to_gbp
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://collectingcars.com"

UK_MARKET_TERMS = {
    "uk", "united kingdom", "great britain", "gb",
    "england", "scotland", "wales", "northern ireland",
}

# Category pages to pull listing links from — currently just DB9, matching
# the single tracked hunt. The numeric IDs in the path are Collecting
# Cars' own internal taxonomy IDs for make/model; fragile if they ever
# change, but confirmed live and working today.
CATEGORY_PATHS = [
    "/makes/Aston-Martin/59/DB9/1473",
]


@register_scraper("collecting_cars")
class CollectingCarsScraper(BaseScraper):
    source_name = "collecting_cars"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client) -> list[RawListing]:
        all_listings: list[RawListing] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = await browser.new_page(user_agent=self.user_agent)

                slugs: set[str] = set()
                for path in CATEGORY_PATHS:
                    try:
                        await page.goto(urljoin(BASE_URL, path), timeout=30000, wait_until="domcontentloaded")
                        # Cloudflare's challenge resolves client-side —
                        # confirmed live it needs a few seconds beyond
                        # plain DOM-ready before the real page replaces it.
                        await page.wait_for_timeout(6000)
                        html = await page.content()
                        found = set(re.findall(r"/for-sale/([a-z0-9-]+)", html))
                        slugs.update(found)
                        logger.info(f"[CollectingCars] {path}: found {len(found)} listing links")
                    except Exception as e:
                        logger.error(f"[CollectingCars] Failed to fetch category {path}: {e}")

                for slug in slugs:
                    try:
                        listing = await self._fetch_listing(page, slug)
                        if listing:
                            all_listings.append(listing)
                    except Exception as e:
                        logger.debug(f"[CollectingCars] Error on listing {slug}: {e}")
                    await asyncio.sleep(1.5)
            finally:
                await browser.close()

        return all_listings

    async def _fetch_listing(self, page, slug: str) -> RawListing | None:
        url = f"{BASE_URL}/for-sale/{slug}"
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        title_el = soup.select_one('meta[property="og:title"]')
        title = clean_text(title_el["content"]) if title_el and title_el.get("content") else None
        if not title or len(title) < 5:
            return None

        # Stable-ish: the hashed CSS-module class prefix can change between
        # site deploys, so match on the "__label"/"__value" suffix with a
        # substring selector rather than the exact hash.
        spec: dict[str, str] = {}
        for item in soup.select('div[class*="gridItem"]'):
            label_el = item.select_one('span[class*="__label"]')
            value_el = item.select_one('span[class*="__value"]')
            if label_el and value_el:
                key = clean_text(label_el.get_text())
                if key:
                    spec[key.lower()] = clean_text(value_el.get_text())

        original_market = spec.get("original market")
        if original_market and original_market.strip().lower() not in UK_MARKET_TERMS:
            logger.info(f"[CollectingCars] Skipping {slug}: non-UK original market ({original_market!r})")
            return None

        year = parse_year(title)
        mileage, mileage_unit = parse_mileage(spec.get("mileage")) if spec.get("mileage") else (None, "miles")

        price = None
        currency = "GBP"
        bid_el = soup.select_one('div[class*="stickyCurrentBid"]')
        if bid_el:
            bid_text = clean_text(bid_el.get_text()) or ""
            currency = detect_currency(bid_text)
            price = parse_price(bid_text)
            if price is not None and currency != "GBP":
                price = to_gbp(price, currency)

        description_parts = []
        for heading_text in ("Key facts", "Equipment and features"):
            heading = soup.find(lambda tag: tag.name in ("h2", "h3") and tag.get_text(strip=True) == heading_text)
            if heading:
                ul = heading.find_next_sibling("ul")
                if ul:
                    description_parts.extend(clean_text(li.get_text()) for li in ul.find_all("li"))
        description = " ".join(p for p in description_parts if p)[:2000] or None

        img_el = soup.select_one('meta[property="og:image"]')
        image_urls = [img_el["content"]] if img_el and img_el.get("content") else []

        make, model = extract_make_model(title, year)

        return RawListing(
            external_id=slug,
            title=title[:500],
            listing_url=url,
            listing_type="auction",
            make=make,
            model=model,
            year=year,
            asking_price=price,
            currency="GBP",
            price_gbp=price,
            mileage=mileage,
            mileage_unit=mileage_unit,
            color=spec.get("exterior"),
            transmission=None,
            location=original_market or spec.get("registration"),
            description=description,
            image_urls=image_urls,
        )

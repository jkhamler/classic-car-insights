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

Each category-page card's auction state (Live/"Current bid", "Coming
Soon", or "Sold") is read directly off the card text at discovery time,
and anything already "Sold" there is dropped before it's even fetched —
per explicit request, only verified live-bidding or coming-soon lots
should ever count. Without this, a Sold lot stays linked from the
category page's own Sold carousel indefinitely, so every scrape kept
re-seeing (and so never delisting) cars that had actually sold months
earlier — confirmed live on several DB9 lots still marked "active" in
our DB that the site itself shows "Sold" back in Jan-Sep 2026.

No reliable per-listing private/trade seller signal: the "consignor"
shown on every listing is a Collecting Cars staff member facilitating
the sale, not the actual owner — same ambiguity as the UK auction houses
(Historics, Mathewsons, etc.), so seller_type is left unset here too.

Collecting Cars is UK/EU, not UK-only. The DB9 hunt is a UK "55 plate"
car specifically, so a continental-market DB9 (e.g. an Italian-market
car, confirmed live via a listing with "Original market: Italy" and km
mileage, no UK registration field at all) must not count even though its
year/model matches — but this is a DB9-only constraint, not a site-wide
one (the 996 Turbo hunt has no country restriction), so the "Original
market" check below only runs when the matched model is DB9. Genuine UK
cars show a "Registration" field with a UK plate instead of "Original
market", so any non-UK "Original market" value rejects the DB9 listing
outright; absent that field, benefit of the doubt applies like the year
gate elsewhere.
"""
import asyncio
import logging
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

# Category pages to pull listing links from. The numeric IDs in each path
# are Collecting Cars' own internal taxonomy IDs for make/model; fragile if
# they ever change, but confirmed live and working today. The 911 page
# covers every generation/trim — extract_make_model() narrows it to 996
# Turbo only after fetching, same as every other source.
CATEGORY_PATHS = [
    "/makes/Aston-Martin/59/DB9/1473",
    "/makes/Porsche/1/911/5",
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
                # slug -> state ("live" | "coming_soon" | "sold"), merged
                # across every category page (a slug appearing live on one
                # page always wins over seeing it sold on another, though
                # that shouldn't happen in practice).
                slug_states: dict[str, str] = {}
                for path in CATEGORY_PATHS:
                    # A fresh tab per category path — confirmed live that
                    # navigating a second category page in the same tab
                    # that already loaded one gets permanently Cloudflare-
                    # challenged (even across retries), while the exact
                    # same URL in a brand-new tab on the same browser loads
                    # clean first try. Listing-detail fetches don't hit
                    # this, so they stay on a shared tab below.
                    cat_page = await browser.new_page(user_agent=self.user_agent)
                    try:
                        html = ""
                        for attempt in range(3):
                            await cat_page.goto(urljoin(BASE_URL, path), timeout=30000, wait_until="domcontentloaded")
                            await cat_page.wait_for_timeout(6000)
                            html = await cat_page.content()
                            if "Just a moment" not in html:
                                break
                        else:
                            logger.error(f"[CollectingCars] {path}: still Cloudflare-challenged after 3 attempts, skipping")
                            continue
                        found = self._parse_category_cards(html)
                        for slug, state in found.items():
                            if slug_states.get(slug) != "live":
                                slug_states[slug] = state
                        logger.info(f"[CollectingCars] {path}: found {len(found)} cards")
                    except Exception as e:
                        logger.error(f"[CollectingCars] Failed to fetch category {path}: {e}")
                    finally:
                        await cat_page.close()

                page = await browser.new_page(user_agent=self.user_agent)

                sold = {s for s, state in slug_states.items() if state == "sold"}
                if sold:
                    logger.info(f"[CollectingCars] Skipping {len(sold)} already-sold lots")

                for slug, state in slug_states.items():
                    if state == "sold":
                        continue
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

    @staticmethod
    def _parse_category_cards(html: str) -> dict[str, str]:
        """Extract {slug: state} from a category page. State is read off
        each card's own text ("Current bid..." = live, "Coming Soon" =
        coming_soon, "Sold..." = sold) rather than the individual listing
        page, since a Sold lot stays linked from the category page's Sold
        carousel long after the sale — reading it here is what lets a sold
        lot be skipped before ever fetching its page.
        """
        soup = BeautifulSoup(html, "lxml")
        states: dict[str, str] = {}
        for a in soup.select('a[href*="/for-sale/"]'):
            href = a.get("href") or ""
            slug = href.rsplit("/for-sale/", 1)[-1].strip("/")
            if not slug or slug in states:
                continue
            # Each card sits in a <swiper-slide> element — sometimes the
            # tag itself, sometimes a div carrying a "swiper-slide*" class
            # (active/next/prev) — which is the one ancestor whose text is
            # just this one card, not the whole carousel.
            node, slide = a, None
            for _ in range(8):
                node = node.parent
                if node is None:
                    break
                classes = node.get("class") or []
                if node.name == "swiper-slide" or any(c.startswith("swiper-slide") for c in classes):
                    slide = node
                    break
            text = slide.get_text(" ", strip=True) if slide else ""
            if "sold" in text.lower():
                state = "sold"
            elif "coming soon" in text.lower():
                state = "coming_soon"
            else:
                # Benefit of the doubt when the slide wrapper wasn't found
                # or its text is ambiguous — same pattern as the year gate.
                state = "live"
            states[slug] = state
        return states

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

        year = parse_year(title)
        make, model = extract_make_model(title, year)

        # DB9-only constraint (the hunt is specifically a UK "55 plate"
        # car) — the 996 Turbo hunt has no country restriction, so this
        # must not reject non-UK listings of anything else.
        original_market = spec.get("original market")
        if model == "DB9" and original_market and original_market.strip().lower() not in UK_MARKET_TERMS:
            logger.info(f"[CollectingCars] Skipping {slug}: non-UK original market ({original_market!r})")
            return None

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

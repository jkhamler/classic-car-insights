"""AutoTrader UK — the mainstream national marketplace, deliberately added
despite the platform's usual niche-only bias: for DB9 specifically, the
cheap end of the market (sub-£25k) turned out to sit almost entirely on
mainstream aggregators, and AutoTrader is the only one of those that's
actually scrapeable (Car & Classic and Cazoo are both behind bot-challenge
walls; eBay 403s).

Search results are rendered client-side (no data in the initial HTML), so
this uses Playwright instead of plain httpx — the one scraper in this
codebase that needs a real browser. Card markup uses stable `data-testid`
attributes; the surrounding class names are styled-components hashes that
change on every AutoTrader deploy, so those are avoided entirely.

Nationwide search: a fixed central postcode with a 1500-mile radius (more
than the UK's longest possible span), so results aren't biased toward one
region. Confirmed live: 83 UK results for "DB9" alone, ~21 per page.
"""
import asyncio
import logging
import re
from urllib.parse import urljoin

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.utils import parse_price, parse_year, parse_mileage, clean_text
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.autotrader.co.uk"
SEARCH_POSTCODE = "SW1A1AA"
SEARCH_RADIUS_MILES = 1500
MAX_PAGES = 5

# (make, model) pairs as AutoTrader's own search taxonomy spells them.
# "Vantage" covers V8/V12 and both generations — extract_make_model()'s
# v8+roadster+year gate narrows it down after fetching, same pattern as
# "SL" covering every SL generation down to just R107.
SEARCHES = [
    ("Aston Martin", "DB9"),
    ("Aston Martin", "Vantage"),
    ("Mercedes-Benz", "SL"),
]


@register_scraper("autotrader")
class AutoTraderScraper(BaseScraper):
    source_name = "autotrader"
    rate_limit_seconds = 3.0

    async def scrape_listings(self, client) -> list[RawListing]:
        all_listings: list[RawListing] = []
        seen_ids: set[str] = set()
        fetch_errors: list[str] = []

        async with async_playwright() as p:
            # --no-sandbox/--disable-dev-shm-usage: Chromium's default
            # sandbox needs kernel privileges most containers don't grant —
            # without these it can fail on every page load rather than at
            # launch, which otherwise silently produces zero results instead
            # of a clear error.
            browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = await browser.new_page(user_agent=self.user_agent)
                for make, model in SEARCHES:
                    for page_num in range(1, MAX_PAGES + 1):
                        url = (
                            f"{BASE_URL}/car-search?postcode={SEARCH_POSTCODE}"
                            f"&make={make.replace(' ', '%20')}&model={model}"
                            f"&radius={SEARCH_RADIUS_MILES}&page={page_num}"
                        )
                        try:
                            # "networkidle" is unreliable here — the page
                            # has persistent background analytics traffic
                            # that never goes fully quiet, and it timed out
                            # every time from Railway's network path (worked
                            # fine locally). Wait for the DOM instead, then
                            # explicitly wait for the listing cards (or the
                            # result-count element, present even on a
                            # genuine zero-result search) to actually render.
                            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                            try:
                                await page.wait_for_selector(
                                    'li[data-advertid], [data-testid="search-result-count"]',
                                    timeout=15000,
                                )
                            except Exception:
                                pass  # proceed with whatever rendered — parsed as 0 cards if nothing did
                            html = await page.content()
                        except Exception as e:
                            msg = f"{make} {model} page={page_num}: fetch failed: {e}"
                            logger.error(f"[AutoTrader] {msg}")
                            fetch_errors.append(msg)
                            break

                        cards = self._parse_page(html, seen_ids)
                        if not cards and page_num > 1:
                            break
                        # The search card carries no description at all —
                        # the seller's actual condition notes only live on
                        # the listing's own page (confirmed live: a "40%
                        # below benchmark" Vantage Roadster's description
                        # turned out to mention a broken seat control unit
                        # and a service coming due). Only worth the extra
                        # page load for cars that actually matched one of
                        # our tracked models, not every raw search result.
                        for listing in cards:
                            if listing.model:
                                listing.description = await self._fetch_description(page, listing.listing_url)
                                await asyncio.sleep(1.0)
                        all_listings.extend(cards)
                        logger.info(f"[AutoTrader] {make} {model} page={page_num}: found {len(cards)}")
                        if len(cards) < 15:  # fewer than a near-full page — no more results
                            break
            finally:
                await browser.close()

        # Every search's very first page failing, with nothing at all
        # found, is much more likely a broken browser/navigation than a
        # genuine zero-result day — raise so it surfaces as a failed
        # scrape_run instead of silently recording "0 found, success".
        if not all_listings and len(fetch_errors) >= len(SEARCHES):
            raise RuntimeError(f"AutoTrader: every search failed to load; first error: {fetch_errors[0]}")

        return all_listings

    async def _fetch_description(self, page, url: str) -> str | None:
        try:
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            try:
                await page.wait_for_selector('[data-testid="description"]', timeout=8000)
            except Exception:
                return None  # some ads genuinely have no description section
            el = await page.query_selector('[data-testid="description"] p')
            if not el:
                return None
            text = await el.inner_text()
            return clean_text(text)[:2000] if text else None
        except Exception as e:
            logger.debug(f"[AutoTrader] description fetch failed for {url}: {e}")
            return None

    def _parse_page(self, html: str, seen_ids: set[str]) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("li[data-advertid]"):
            try:
                advert_id = card.get("data-advertid")
                if not advert_id or advert_id in seen_ids:
                    continue

                title_el = card.select_one('[data-testid="search-listing-title"]')
                if not title_el:
                    continue
                href = urljoin(BASE_URL, title_el.get("href", ""))

                # The visible heading is just "<Make> <Model>" (e.g. "Aston
                # Martin DB9"); the full spec + price live in a visually-
                # hidden span inside the same link, e.g. "5.9 Volante Seq
                # 2dr (EU4), £19,300" — split price out of that rather than
                # the unstable price <span>'s class name. Pull its text out
                # first, then decompose it so get_text() on the link leaves
                # just the heading.
                hidden_span = title_el.select_one("span")
                spec_and_price = clean_text(hidden_span.get_text()) if hidden_span else ""
                if hidden_span:
                    hidden_span.decompose()
                heading = clean_text(title_el.get_text(separator=" ", strip=True))

                price = None
                price_match = re.search(r"£\s*([\d,]+)", spec_and_price or "")
                if price_match:
                    price = parse_price(f"£{price_match.group(1)}")

                subtitle_el = card.select_one('[data-testid="search-listing-subtitle"]')
                subtitle = clean_text(subtitle_el.get_text()) if subtitle_el else ""

                title = clean_text(f"{heading or ''} {subtitle or ''}".strip())
                if not title or len(title) < 5:
                    continue
                seen_ids.add(advert_id)

                year_el = card.select_one('[data-testid="registered_year"]')
                year = parse_year(year_el.get_text()) if year_el else None

                mileage_el = card.select_one('[data-testid="mileage"]')
                mileage, mileage_unit = (
                    parse_mileage(mileage_el.get_text()) if mileage_el else (None, "miles")
                )

                location_el = card.select_one('[data-testid="search-listing-location"]')
                location = None
                if location_el:
                    for svg in location_el.select("svg"):
                        svg.decompose()
                    location = clean_text(location_el.get_text())

                make, model = extract_make_model(title)

                seller_type = "private" if card.select_one('[data-testid="private-seller"]') else "trade"

                img_el = card.select_one("img[src]")
                image_urls = [img_el["src"]] if img_el and img_el.get("src") else []

                listings.append(RawListing(
                    external_id=str(advert_id),
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
                    seller_type=seller_type,
                    location=location,
                    image_urls=image_urls,
                ))
            except Exception as e:
                logger.debug(f"[AutoTrader] Error parsing card: {e}")
                continue

        return listings

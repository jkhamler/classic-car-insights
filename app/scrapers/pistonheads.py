"""PistonHeads scraper — classifieds + auctions, private sellers only.

PistonHeads migrated its classifieds to a JS-rendered Next.js app, which is
why the old CSS-selector scraper silently returned 0 results. But the
server-rendered HTML for /buy/<make>/<model> and /buy/auctions still embeds
a full Apollo GraphQL cache (__NEXT_DATA__ -> props.pageProps.
__APOLLO_STATE__) with real Advert/Seller objects, including seller.
sellerType ("Private" vs "Trade") — no need for the client-side GraphQL API,
which rejects unrecognized (non-persisted) queries.

Only the first page of results per URL is available this way (~16 listings);
paging further requires that same gated API. Acceptable here since our
tracked models are narrow enough that most fit on one page.
"""
import json
import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import httpx

from app.scrapers.base import BaseScraper, RawListing
from app.scrapers.registry import register_scraper
from app.scrapers.vehicle_targets import extract_make_model

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pistonheads.com"

# PistonHeads' own taxonomy splits generations/trims finely enough to target
# directly, cutting an otherwise-enormous "all Porsche" sweep down to just
# what we track.
MODEL_PATHS = [
    "/buy/porsche/911-turbo-996",
    "/buy/porsche/911-carrera-996",
    "/buy/bmw/z3m-coupe",
    "/buy/bmw/z3m-roadster",
    "/buy/bmw/z4m-coupe",
    "/buy/bmw/z4m-roadster",
    "/buy/mercedes-benz/280sl",
    "/buy/mercedes-benz/300sl",
    "/buy/mercedes-benz/350sl",
    "/buy/tvr/t350",
]

# Cross-make browse page for current live auctions — a model-scoped /buy/
# path above won't surface an auction lot unless it happens to also be the
# newest listing in that model's first page, so this is checked separately.
AUCTIONS_PATH = "/buy/auctions"

NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


@register_scraper("pistonheads")
class PistonHeadsScraper(BaseScraper):
    source_name = "pistonheads"
    rate_limit_seconds = 2.5

    async def scrape_listings(self, client: httpx.AsyncClient) -> list[RawListing]:
        all_listings: list[RawListing] = []
        seen_ids: set[str] = set()

        for path in MODEL_PATHS + [AUCTIONS_PATH]:
            try:
                html = await self.fetch_with_rate_limit(client, urljoin(BASE_URL, path))
                listings = self._parse_page(html, seen_ids)
                all_listings.extend(listings)
                logger.info(f"[PistonHeads] {path}: found {len(listings)} private listings")
            except Exception as e:
                logger.error(f"[PistonHeads] Failed to scrape {path}: {e}")

        return all_listings

    def _parse_page(self, html: str, seen_ids: set[str]) -> list[RawListing]:
        match = NEXT_DATA_RE.search(html)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        apollo = data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
        listings = []

        for key, obj in apollo.items():
            if not key.startswith("Advert:") or not isinstance(obj, dict):
                continue
            advert_id = obj.get("id")
            if not advert_id or advert_id in seen_ids:
                continue

            seller_ref = (obj.get("seller") or {}).get("__ref")
            seller = apollo.get(seller_ref, {}) if seller_ref else {}
            if seller.get("sellerType") != "Private":
                continue  # dealers/trade excluded — private sellers only

            title = obj.get("headline")
            make, model = extract_make_model(title)
            if not model:
                continue  # not one of our tracked models

            # specificationData is sometimes inlined, sometimes a separate
            # normalized cache entry referenced by __ref — handle both.
            spec_raw = obj.get("specificationData") or {}
            spec_ref = spec_raw.get("__ref")
            spec = apollo.get(spec_ref, {}) if spec_ref else spec_raw

            # auctionDetails is only present for auction lots. Its "price"
            # field is unrelated/unreliable for these (0 or null in the
            # /buy/auctions query) — use the live highestBid instead, and
            # skip anything not currently LIVE (ended-but-still-listed lots).
            auction_raw = obj.get("auctionDetails") or {}
            auction_ref = auction_raw.get("__ref")
            auction = apollo.get(auction_ref, {}) if auction_ref else auction_raw
            is_auction = bool(auction)
            if is_auction and auction.get("displayStatus") != "LIVE":
                continue

            seen_ids.add(advert_id)

            price = auction.get("highestBid") if is_auction else obj.get("price")
            currency = obj.get("currencyCode") or "GBP"

            listings.append(RawListing(
                external_id=str(advert_id),
                title=title[:500],
                listing_url=obj.get("url") or f"{BASE_URL}/buy/listing/{advert_id}",
                listing_type="auction" if is_auction else "classified",
                make=make,
                model=model,
                year=obj.get("year"),
                asking_price=price,
                currency=currency,
                price_gbp=price if currency == "GBP" else None,
                mileage=spec.get("mileage"),
                mileage_unit="miles",
                transmission=spec.get("transmissionType"),
                color=spec.get("colour"),
                location=seller.get("location"),
                image_urls=obj.get("fullSizeImageUrls") or [],
                auction_end_at=self._parse_iso(auction.get("endDateTime")) if is_auction else None,
            ))

        return listings

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

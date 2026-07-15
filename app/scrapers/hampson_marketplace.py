"""Hampson Marketplace — Bidpath-powered UK auction house."""
from app.scrapers.bidpath_base import BidpathScraper
from app.scrapers.registry import register_scraper


@register_scraper("hampson_marketplace")
class HampsonMarketplaceScraper(BidpathScraper):
    source_name = "hampson_marketplace"
    base_url = "https://hampson.go-auction.com"

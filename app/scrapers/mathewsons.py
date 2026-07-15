"""Mathewsons — Bidpath-powered UK auction house."""
from app.scrapers.bidpath_base import BidpathScraper
from app.scrapers.registry import register_scraper


@register_scraper("mathewsons")
class MathewsonsScraper(BidpathScraper):
    source_name = "mathewsons"
    base_url = "https://www.mathewsons.co.uk"

"""Manor Park Classics — Bidpath-powered UK auction house."""
from app.scrapers.bidpath_base import BidpathScraper
from app.scrapers.registry import register_scraper


@register_scraper("manor_park")
class ManorParkScraper(BidpathScraper):
    source_name = "manor_park"
    base_url = "https://www.manorparkclassics.com"

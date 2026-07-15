"""Historics Auctioneers — Bidpath-powered UK auction house (higher-end classics)."""
from app.scrapers.bidpath_base import BidpathScraper
from app.scrapers.registry import register_scraper


@register_scraper("historics")
class HistoricsScraper(BidpathScraper):
    source_name = "historics"
    base_url = "https://www.historics.co.uk"

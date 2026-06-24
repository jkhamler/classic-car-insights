"""Scraper registry — maps source names to scraper classes."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.scrapers.base import BaseScraper

SCRAPER_REGISTRY: dict[str, type["BaseScraper"]] = {}


def register_scraper(source_name: str):
    def decorator(cls):
        SCRAPER_REGISTRY[source_name] = cls
        return cls
    return decorator


def get_scraper_class(source_name: str) -> type["BaseScraper"] | None:
    return SCRAPER_REGISTRY.get(source_name)


def get_available_scrapers() -> list[str]:
    return list(SCRAPER_REGISTRY.keys())

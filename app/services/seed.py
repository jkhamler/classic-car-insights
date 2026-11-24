"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Mercedes-Benz S500 Coupe (C217 generation), 2015 onwards — open-ended,
    # no upper year bound, per explicit request, replacing the earlier
    # Aston Martin modern-classics hunt. See vehicle_targets.py for why the
    # "S500"+"coupe" text match (rather than just the year gate) is what
    # actually disambiguates this from the contemporary W222 S-Class
    # saloon, which shares the same "S500" badge. No price/mileage
    # ceilings or scoring bonuses set yet — no budget or feature
    # preference has been stated.
    VehicleCreate(make="Mercedes-Benz", model="S500 Coupe", year_start=2015, year_end=None, country_of_origin="Germany", segment="grand tourer", body_style="coupe", engine_type="4.7L Twin-Turbo V8"),
]

# Mainstream classifieds only — like the SL400 hunt before it, the S500
# Coupe is a mainstream depreciation-curve luxury GT, not a collector
# piece, so ordinary dealer/private-seller classifieds (not niche
# auction houses or marque specialists) are where real supply lives.
SEED_SOURCES = [
    SourceCreate(
        name="gumtree",
        display_name="Gumtree",
        source_type="discovery",
        base_url="https://www.gumtree.com",
        scraper_class="GumtreeScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="pistonheads",
        display_name="PistonHeads",
        source_type="discovery",
        base_url="https://www.pistonheads.com",
        scraper_class="PistonHeadsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="autotrader",
        display_name="AutoTrader UK",
        source_type="discovery",
        base_url="https://www.autotrader.co.uk",
        scraper_class="AutoTraderScraper",
        scrape_frequency_minutes=360,
    ),
]


def seed_vehicles(db: Session) -> int:
    created = 0
    for v in SEED_VEHICLES:
        existing = get_vehicle_by_identity(db, v.make, v.model, v.generation)
        if not existing:
            create_vehicle(db, v)
            created += 1
    return created


def seed_sources(db: Session) -> int:
    created = 0
    for s in SEED_SOURCES:
        get_or_create_source(db, s)
        created += 1
    return created


def seed_all(db: Session) -> dict:
    vehicles_created = seed_vehicles(db)
    sources_created = seed_sources(db)
    return {
        "vehicles_created": vehicles_created,
        "sources_created": sources_created,
    }

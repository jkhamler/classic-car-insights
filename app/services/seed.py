"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Mercedes-Benz SL400 (R231 generation), 2015 onwards — open-ended,
    # no upper year bound, per explicit request. Under £18k, under 80k
    # miles, private sellers only, dark exterior over light interior hard
    # gates; Harman Kardon audio and AIRSCARF are a scoring bonus, not a
    # gate (all in vehicle_targets.py — the price/mileage/seller-type
    # ceilings and the required/bonus text groups). The only model
    # tracked now — SL350 was tracked alongside it briefly for a direct
    # cross-shop comparison, then dropped per explicit follow-up once
    # SL400 was settled on as the sole model of interest. Mainstream
    # depreciation-curve car, not a collector piece, hence the mainstream-
    # classifieds-only source list in seed.py's SEED_SOURCES below.
    VehicleCreate(make="Mercedes-Benz", model="SL400", year_start=2015, year_end=None, country_of_origin="Germany", segment="grand tourer", body_style="convertible", engine_type="3.0L V6 Biturbo"),
]

# Mainstream classifieds only — the SL400 hunt is a mainstream
# depreciation-curve car, not a collector piece, so the niche classic-
# auction houses (Trade Classics, Hampson, Mathewsons, Historics, Anglia,
# Morris Leslie, Manor Park, Charterhouse, Collecting Cars) and marque-club/
# specialist sources (AMOC, Nicholas Mee, Prestige Automotives) dropped
# here carry essentially zero SL400 stock. Bring a Trailer (both the US
# site and UK hub) is dropped too as a benchmark source for the same
# reason — it's a US-skewed enthusiast/collector auction site with little
# to no SL400 comp volume; benchmark_calculator.py's
# existing fallback (median of live active-listing asking prices, any
# source) stands in as the fair-value baseline instead, which is the
# honest comparison for a car like this anyway. A Copart UK salvage source
# was considered (user is open to salvage) but dropped — it sits behind an
# Imperva/hCaptcha bot wall, confirmed live, and SYNETIQ no longer runs a
# public vehicle-for-sale search (parts only now).
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

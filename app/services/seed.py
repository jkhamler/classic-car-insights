"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Aston Martin "modern classics" selection, per explicit request,
    # replacing the earlier Mercedes-Benz SL400 hunt. Four distinct
    # generations, closed year ranges (see vehicle_targets.py for why the
    # year gate matters here — "Vantage" and "DBS" are both reused Aston
    # names across eras). No price/mileage ceilings or feature bonuses set
    # yet for any of these — no budget or preference has been stated, so
    # undervaluation is left entirely to scoring.py's benchmark comparison.
    VehicleCreate(make="Aston Martin", model="DB7", year_start=1994, year_end=2003, country_of_origin="United Kingdom", segment="grand tourer", body_style="coupe", engine_type="3.2L Supercharged I6 / 5.9L V12 (Vantage)"),
    VehicleCreate(make="Aston Martin", model="DB9", year_start=2004, year_end=2016, country_of_origin="United Kingdom", segment="grand tourer", body_style="coupe", engine_type="5.9L V12"),
    VehicleCreate(make="Aston Martin", model="V8 Vantage", year_start=2005, year_end=2017, country_of_origin="United Kingdom", segment="sports car", body_style="coupe", engine_type="4.3L/4.7L V8"),
    VehicleCreate(make="Aston Martin", model="DBS", year_start=2007, year_end=2012, country_of_origin="United Kingdom", segment="grand tourer", body_style="coupe", engine_type="6.0L V12"),
]

# Mix of mainstream classifieds (still worth covering — DB9/V8 Vantage in
# particular show up on ordinary classifieds, not just specialist
# channels) and Aston-specific/collector sources, since these are more
# collector-oriented than the old SL400 depreciation-curve hunt: AMOC
# (Aston Martin Owners Club classifieds), Nicholas Mee (long-established
# Aston specialist dealer), and Collecting Cars (enthusiast consignment
# auction site with strong classic/modern-classic Aston volume). Bring a
# Trailer is the benchmark source — unlike the SL400 hunt (where it was
# dropped for near-zero UK SL400 volume), Astons are exactly the kind of
# car BaT carries good UK-location sold-comp data for.
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
    SourceCreate(
        name="amoc",
        display_name="AMOC Classifieds",
        source_type="discovery",
        base_url="https://amoc.org",
        scraper_class="AMOCScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="nicholas_mee",
        display_name="Nicholas Mee & Co",
        source_type="discovery",
        base_url="https://www.nicholasmee.co.uk",
        scraper_class="NicholasMeeScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="collecting_cars",
        display_name="Collecting Cars",
        source_type="discovery",
        base_url="https://collectingcars.com",
        scraper_class="CollectingCarsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="bring_a_trailer",
        display_name="Bring a Trailer (UK)",
        source_type="benchmark",
        base_url="https://bringatrailer.com",
        scraper_class="BringATrailerScraper",
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

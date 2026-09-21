"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Mercedes-Benz SL-Class R107 — 1986-1989 build years only (see
    # vehicle_targets.py for why: only badges still in production in that
    # window are tracked). No price/mileage ceiling set for this hunt.
    VehicleCreate(make="Mercedes-Benz", model="SL", generation="R107", year_start=1986, year_end=1989, country_of_origin="Germany", segment="convertible", body_style="roadster", engine_type="I6/V8 (3.0L-5.6L)"),
    # Aston Martin DB9 — full production run, coupe and Volante convertible.
    # No price/mileage ceiling set for this hunt.
    VehicleCreate(make="Aston Martin", model="DB9", year_start=2004, year_end=2016, country_of_origin="United Kingdom", segment="grand tourer", body_style="coupe/convertible", engine_type="V12 (5.9L)"),
]

SEED_SOURCES = [
    SourceCreate(
        name="bring_a_trailer",
        display_name="Bring a Trailer (UK)",
        source_type="benchmark",
        base_url="https://bringatrailer.com",
        scraper_class="BringATrailerScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="bring_a_trailer_uk",
        display_name="Bring a Trailer (UK Hub)",
        source_type="benchmark",
        base_url="https://bringatrailer.com/uk",
        scraper_class="BringATrailerUKScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="trade_classics",
        display_name="Trade Classics",
        source_type="discovery",
        base_url="https://www.tradeclassics.com",
        scraper_class="TradeClassicsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="hampson_marketplace",
        display_name="Hampson Marketplace",
        source_type="discovery",
        base_url="https://hampson.go-auction.com",
        scraper_class="HampsonMarketplaceScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="mathewsons",
        display_name="Mathewsons",
        source_type="discovery",
        base_url="https://www.mathewsons.co.uk",
        scraper_class="MathewsonsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="historics",
        display_name="Historics Auctioneers",
        source_type="discovery",
        base_url="https://www.historics.co.uk",
        scraper_class="HistoricsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="anglia_car_auctions",
        display_name="Anglia Car Auctions",
        source_type="discovery",
        base_url="https://www.angliacarauctions.co.uk",
        scraper_class="AngliaCarAuctionsScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="morris_leslie",
        display_name="Morris Leslie Auctions",
        source_type="discovery",
        base_url="https://auction.morrisleslie.com",
        scraper_class="MorrisLeslieScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="manor_park",
        display_name="Manor Park Classics",
        source_type="discovery",
        base_url="https://www.manorparkclassics.com",
        scraper_class="ManorParkScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="charterhouse",
        display_name="Charterhouse Auctioneers",
        source_type="discovery",
        base_url="https://charterhouse-cars.com",
        scraper_class="CharterhouseScraper",
        scrape_frequency_minutes=360,
    ),
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
        name="prestige_automotives",
        display_name="Prestige Automotives (Japanese Import Specialist)",
        source_type="discovery",
        base_url="https://www.prestige-automotives.co.uk",
        scraper_class="PrestigeAutomotivesScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="amoc",
        display_name="Aston Martin Owners Club Classifieds",
        source_type="discovery",
        base_url="https://amoc.org",
        scraper_class="AMOCScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="nicholas_mee",
        display_name="Nicholas Mee & Co (Aston Martin Specialist)",
        source_type="discovery",
        base_url="https://www.nicholasmee.co.uk",
        scraper_class="NicholasMeeScraper",
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

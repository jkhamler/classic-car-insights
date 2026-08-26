"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Volvo V70 / XC70 — Japanese-import grey imports only, 2.5T five-cylinder
    # preferred, budget capped at MAX_DISCOVERY_PRICE_GBP (see vehicle_targets.py).
    VehicleCreate(make="Volvo", model="V70", generation="P2", year_start=2000, year_end=2007, country_of_origin="Sweden", segment="estate", body_style="estate", engine_type="2.5L Turbo I5 (2.5T)"),
    VehicleCreate(make="Volvo", model="V70", generation="P3", year_start=2007, year_end=2016, country_of_origin="Sweden", segment="estate", body_style="estate", engine_type="2.5L Turbo I5 (2.5T, 2007-2009) / T5 / T6 / D5"),
    VehicleCreate(make="Volvo", model="XC70", generation="P2", year_start=2000, year_end=2007, country_of_origin="Sweden", segment="estate", body_style="estate (AWD)", engine_type="2.5L Turbo I5 (2.5T)"),
    VehicleCreate(make="Volvo", model="XC70", generation="P3", year_start=2007, year_end=2016, country_of_origin="Sweden", segment="estate", body_style="estate (AWD)", engine_type="2.5L Turbo I5 (2.5T, 2007-2009) / T5 / T6 / D5"),
]

SEED_SOURCES = [
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

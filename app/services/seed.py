"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Porsche 911 996 Turbo only
    VehicleCreate(make="Porsche", model="911", generation="996", year_start=1998, year_end=2004, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.6L Twin-Turbo Flat-6"),

    # BMW Z4 M
    VehicleCreate(make="BMW", model="Z4 M", generation="E85/E86", year_start=2006, year_end=2008, country_of_origin="Germany", segment="sports_car", body_style="coupe/roadster", engine_type="3.2L I6"),

    # TVR T350 — both T350C (coupe) and T350T (targa)
    VehicleCreate(make="TVR", model="T350", generation="T350", year_start=2002, year_end=2006, country_of_origin="UK", segment="sports_car", body_style="coupe/targa", engine_type="3.6L Speed Six I6"),

    # Lotus Elise — all generations
    VehicleCreate(make="Lotus", model="Elise", generation="S1", year_start=1996, year_end=2001, country_of_origin="UK", segment="sports_car", body_style="roadster", engine_type="1.8L I4"),
    VehicleCreate(make="Lotus", model="Elise", generation="S2", year_start=2001, year_end=2011, country_of_origin="UK", segment="sports_car", body_style="roadster", engine_type="1.8L I4"),
    VehicleCreate(make="Lotus", model="Elise", generation="S3", year_start=2011, year_end=2021, country_of_origin="UK", segment="sports_car", body_style="roadster", engine_type="1.6L/1.8L I4"),
]

SEED_SOURCES = [
    SourceCreate(
        name="bring_a_trailer",
        display_name="Bring a Trailer",
        source_type="benchmark",
        base_url="https://bringatrailer.com",
        scraper_class="BringATrailerScraper",
        scrape_frequency_minutes=720,
    ),
    SourceCreate(
        name="bring_a_trailer_uk",
        display_name="Bring a Trailer (UK)",
        source_type="benchmark",
        base_url="https://bringatrailer.com/uk",
        scraper_class="BringATrailerUKScraper",
        scrape_frequency_minutes=720,
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
        name="porsche_911uk",
        display_name="911uk.com Classifieds",
        source_type="discovery",
        base_url="https://www.911uk.com",
        scraper_class="Porsche911UKScraper",
        scrape_frequency_minutes=360,
    ),
    SourceCreate(
        name="bmw_car_club_gb",
        display_name="BMW Car Club GB Classifieds",
        source_type="discovery",
        base_url="https://bmwcarclubgb.uk",
        scraper_class="BMWCarClubGBScraper",
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
        display_name="PistonHeads (Private Sellers)",
        source_type="discovery",
        base_url="https://www.pistonheads.com",
        scraper_class="PistonHeadsScraper",
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

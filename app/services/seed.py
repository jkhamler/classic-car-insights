"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # Porsche 911 996 — Turbo and Carrera 4S only
    VehicleCreate(make="Porsche", model="911", generation="996", year_start=1998, year_end=2004, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.6L Twin-Turbo Flat-6 (Turbo) / 3.6L Flat-6 (Carrera 4S)"),

    # Audi RS4 / RS6
    VehicleCreate(make="Audi", model="RS4", generation="B5", year_start=2000, year_end=2001, country_of_origin="Germany", segment="sedan", body_style="wagon", engine_type="2.7L Twin-Turbo V6"),
    VehicleCreate(make="Audi", model="RS4", generation="B7", year_start=2006, year_end=2008, country_of_origin="Germany", segment="sedan", body_style="saloon/wagon", engine_type="4.2L V8"),
    VehicleCreate(make="Audi", model="RS4", generation="B8", year_start=2012, year_end=2015, country_of_origin="Germany", segment="sedan", body_style="saloon/wagon", engine_type="4.2L V8"),
    VehicleCreate(make="Audi", model="RS6", generation="C5", year_start=2002, year_end=2004, country_of_origin="Germany", segment="sedan", body_style="saloon/wagon", engine_type="4.2L Twin-Turbo V8"),
    VehicleCreate(make="Audi", model="RS6", generation="C6", year_start=2008, year_end=2010, country_of_origin="Germany", segment="sedan", body_style="saloon/wagon", engine_type="5.0L Twin-Turbo V10"),

    # Alpina
    VehicleCreate(make="Alpina", model="B3", generation="E36", year_start=1994, year_end=1996, country_of_origin="Germany", segment="sports_car", body_style="coupe/convertible", engine_type="3.2L I6"),
    VehicleCreate(make="Alpina", model="B3", generation="E46", year_start=2002, year_end=2006, country_of_origin="Germany", segment="sports_car", body_style="coupe/convertible", engine_type="3.3L I6"),
    VehicleCreate(make="Alpina", model="B3", generation="E90/E92", year_start=2009, year_end=2013, country_of_origin="Germany", segment="sports_car", body_style="coupe/saloon", engine_type="3.0L Bi-Turbo I6"),
    VehicleCreate(make="Alpina", model="B5", generation="E39", year_start=1998, year_end=2003, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="4.8L V8"),
    VehicleCreate(make="Alpina", model="B5", generation="E60", year_start=2007, year_end=2010, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="4.4L Supercharged V8"),
    VehicleCreate(make="Alpina", model="B6", generation="E63", year_start=2007, year_end=2010, country_of_origin="Germany", segment="gt", body_style="coupe/convertible", engine_type="4.4L Supercharged V8"),
    VehicleCreate(make="Alpina", model="B10", generation="E34", year_start=1989, year_end=1994, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="3.5L/3.9L V8"),
    VehicleCreate(make="Alpina", model="B10", generation="E39", year_start=1996, year_end=2002, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="4.6L/4.7L V8"),
    VehicleCreate(make="Alpina", model="D3", generation="E90", year_start=2008, year_end=2012, country_of_origin="Germany", segment="sedan", body_style="sedan/wagon", engine_type="2.0L Bi-Turbo Diesel I4"),

    # BMW Z3 M / Z4 M
    VehicleCreate(make="BMW", model="Z3 M", generation="E36/7-8", year_start=1997, year_end=2002, country_of_origin="Germany", segment="sports_car", body_style="coupe/roadster", engine_type="3.2L I6"),
    VehicleCreate(make="BMW", model="Z4 M", generation="E85/E86", year_start=2006, year_end=2008, country_of_origin="Germany", segment="sports_car", body_style="coupe/roadster", engine_type="3.2L I6"),

    # Aston Martin — DB7 Volante only
    VehicleCreate(make="Aston Martin", model="DB7 Volante", generation="i6/V12 Vantage", year_start=1996, year_end=2003, country_of_origin="UK", segment="gt", body_style="convertible", engine_type="3.2L I6 Supercharged / 5.9L V12"),

    # Japan-import Volvo/BMW/Audi/Mercedes performance
    VehicleCreate(make="Volvo", model="850 T5-R", generation="850", year_start=1994, year_end=1996, country_of_origin="Sweden", segment="sedan", body_style="saloon/wagon", engine_type="2.3L Turbo I5"),
    VehicleCreate(make="Volvo", model="850R", generation="850", year_start=1996, year_end=1997, country_of_origin="Sweden", segment="sedan", body_style="saloon/wagon", engine_type="2.3L Turbo I5"),
    VehicleCreate(make="Volvo", model="S60 R", generation="P2", year_start=2003, year_end=2007, country_of_origin="Sweden", segment="sedan", body_style="sedan", engine_type="2.5L Turbo I5"),
    VehicleCreate(make="Volvo", model="V70 R", generation="P2", year_start=2003, year_end=2007, country_of_origin="Sweden", segment="sedan", body_style="wagon", engine_type="2.5L Turbo I5"),
    VehicleCreate(make="Mercedes-Benz", model="E55 AMG", generation="W210", year_start=1999, year_end=2002, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="5.4L V8"),
    VehicleCreate(make="Mercedes-Benz", model="E55 AMG", generation="W211", year_start=2003, year_end=2006, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="5.4L Supercharged V8"),

    # Mercedes-Benz SL — R107/R129 6-cylinder only (280SL/300SL/320SL badges, no V8)
    VehicleCreate(make="Mercedes-Benz", model="SL", generation="R107", year_start=1971, year_end=1989, country_of_origin="Germany", segment="gt", body_style="convertible", engine_type="2.8L/3.0L I6"),
    VehicleCreate(make="Mercedes-Benz", model="SL", generation="R129", year_start=1989, year_end=2001, country_of_origin="Germany", segment="gt", body_style="convertible", engine_type="2.8L/3.2L I6/V6"),

    # TVR
    VehicleCreate(make="TVR", model="T350", generation="T350", year_start=2002, year_end=2006, country_of_origin="UK", segment="sports_car", body_style="coupe/targa", engine_type="3.6L Speed Six I6"),
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

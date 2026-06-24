"""Seed the database with initial vehicles and sources."""
from sqlalchemy.orm import Session
from app.crud.vehicles import get_vehicle_by_identity, create_vehicle
from app.crud.sources import get_or_create_source
from app.schemas.vehicle import VehicleCreate
from app.schemas.source import SourceCreate

SEED_VEHICLES = [
    # European performance
    VehicleCreate(make="Porsche", model="911", generation="996", year_start=1998, year_end=2004, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.4L/3.6L Flat-6"),
    VehicleCreate(make="Porsche", model="911", generation="997", year_start=2004, year_end=2012, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.6L/3.8L Flat-6"),
    VehicleCreate(make="Porsche", model="Boxster", generation="986", year_start=1996, year_end=2004, country_of_origin="Germany", segment="sports_car", body_style="convertible", engine_type="2.5L/2.7L/3.2L Flat-6"),
    VehicleCreate(make="Porsche", model="Cayman", generation="987", year_start=2005, year_end=2012, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="2.7L/2.9L/3.4L Flat-6"),
    VehicleCreate(make="Porsche", model="944", generation="944", year_start=1982, year_end=1991, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="2.5L/3.0L I4/I4 Turbo"),
    VehicleCreate(make="BMW", model="M3", generation="E36", year_start=1992, year_end=1999, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.0L/3.2L I6"),
    VehicleCreate(make="BMW", model="M3", generation="E46", year_start=2000, year_end=2006, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="3.2L I6"),
    VehicleCreate(make="BMW", model="M3", generation="E90/E92", year_start=2007, year_end=2013, country_of_origin="Germany", segment="sports_car", body_style="coupe", engine_type="4.0L V8"),
    VehicleCreate(make="BMW", model="M5", generation="E39", year_start=1998, year_end=2003, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="4.9L V8"),
    VehicleCreate(make="BMW", model="M5", generation="E60", year_start=2005, year_end=2010, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="5.0L V10"),
    VehicleCreate(make="Mercedes-Benz", model="C63 AMG", generation="W204", year_start=2008, year_end=2014, country_of_origin="Germany", segment="sedan", body_style="sedan", engine_type="6.2L V8"),
    VehicleCreate(make="Mercedes-Benz", model="SL", generation="R129", year_start=1989, year_end=2001, country_of_origin="Germany", segment="gt", body_style="convertible", engine_type="Various V6/V8/V12"),
    VehicleCreate(make="Lotus", model="Elise", generation="S1", year_start=1996, year_end=2001, country_of_origin="UK", segment="sports_car", body_style="convertible", engine_type="1.8L I4"),
    VehicleCreate(make="Lotus", model="Elise", generation="S2", year_start=2001, year_end=2011, country_of_origin="UK", segment="sports_car", body_style="convertible", engine_type="1.8L I4"),
    VehicleCreate(make="Lotus", model="Exige", generation="S2", year_start=2004, year_end=2011, country_of_origin="UK", segment="sports_car", body_style="coupe", engine_type="1.8L I4/Supercharged"),
    VehicleCreate(make="Alfa Romeo", model="GTV", generation="916", year_start=1995, year_end=2006, country_of_origin="Italy", segment="sports_car", body_style="coupe", engine_type="2.0L/3.0L/3.2L V6"),

    # Japanese performance
    VehicleCreate(make="Nissan", model="Skyline GT-R", generation="R32", year_start=1989, year_end=1994, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="2.6L Twin-Turbo I6"),
    VehicleCreate(make="Nissan", model="Skyline GT-R", generation="R33", year_start=1995, year_end=1998, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="2.6L Twin-Turbo I6"),
    VehicleCreate(make="Nissan", model="Skyline GT-R", generation="R34", year_start=1999, year_end=2002, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="2.6L Twin-Turbo I6"),
    VehicleCreate(make="Nissan", model="350Z", generation="Z33", year_start=2002, year_end=2009, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="3.5L V6"),
    VehicleCreate(make="Toyota", model="Supra", generation="A80", year_start=1993, year_end=2002, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="3.0L Twin-Turbo I6"),
    VehicleCreate(make="Toyota", model="MR2", generation="SW20", year_start=1989, year_end=1999, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="2.0L I4/Turbo"),
    VehicleCreate(make="Honda", model="NSX", generation="NA1/NA2", year_start=1990, year_end=2005, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="3.0L/3.2L V6"),
    VehicleCreate(make="Honda", model="S2000", generation="AP1/AP2", year_start=1999, year_end=2009, country_of_origin="Japan", segment="sports_car", body_style="convertible", engine_type="2.0L/2.2L I4"),
    VehicleCreate(make="Honda", model="Integra Type R", generation="DC2", year_start=1995, year_end=2001, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="1.8L I4 VTEC"),
    VehicleCreate(make="Mazda", model="RX-7", generation="FD", year_start=1992, year_end=2002, country_of_origin="Japan", segment="sports_car", body_style="coupe", engine_type="1.3L Twin-Turbo Rotary"),
    VehicleCreate(make="Mazda", model="MX-5", generation="NA", year_start=1989, year_end=1997, country_of_origin="Japan", segment="sports_car", body_style="convertible", engine_type="1.6L/1.8L I4"),
    VehicleCreate(make="Mazda", model="MX-5", generation="NB", year_start=1998, year_end=2005, country_of_origin="Japan", segment="sports_car", body_style="convertible", engine_type="1.6L/1.8L I4"),
    VehicleCreate(make="Mitsubishi", model="Lancer Evolution", generation="VI", year_start=1999, year_end=2001, country_of_origin="Japan", segment="sedan", body_style="sedan", engine_type="2.0L Turbo I4"),
    VehicleCreate(make="Mitsubishi", model="Lancer Evolution", generation="VII-IX", year_start=2001, year_end=2007, country_of_origin="Japan", segment="sedan", body_style="sedan", engine_type="2.0L Turbo I4"),
    VehicleCreate(make="Subaru", model="Impreza WRX STI", generation="GD", year_start=2000, year_end=2007, country_of_origin="Japan", segment="sedan", body_style="sedan", engine_type="2.0L/2.5L Turbo Flat-4"),
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
        name="car_and_classic",
        display_name="Car & Classic",
        source_type="discovery",
        base_url="https://www.carandclassic.com",
        scraper_class="CarAndClassicScraper",
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

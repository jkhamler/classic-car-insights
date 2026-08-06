"""Run one scraper from this machine and write straight into the production
(Railway) database, bypassing Railway's own IP for sources that block its
datacenter range (PistonHeads, 911uk.com) — Railway's scheduled job still
runs everything else daily; this is only for the blocked ones.

Usage:
    poetry run python scripts/scrape_to_prod.py pistonheads

Fetches the production DB URL from the Railway CLI (must be logged in and
linked — `railway status` should show the project) unless DATABASE_URL is
already set in the environment.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _prod_database_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    result = subprocess.run(
        ["railway", "variables", "--service", "Postgres", "--kv"],
        capture_output=True, text=True, check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("DATABASE_PUBLIC_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("DATABASE_PUBLIC_URL not found — is `railway` linked to this project?")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: poetry run python scripts/scrape_to_prod.py <source_name>")
        sys.exit(1)

    # Must set this before importing anything under app/, since app.db.session
    # builds its engine from DATABASE_URL at import time.
    os.environ["DATABASE_URL"] = _prod_database_url()

    import asyncio
    import app.scrapers.bring_a_trailer  # noqa: F401
    import app.scrapers.trade_classics  # noqa: F401
    import app.scrapers.hampson_marketplace  # noqa: F401
    import app.scrapers.mathewsons  # noqa: F401
    import app.scrapers.historics  # noqa: F401
    import app.scrapers.anglia_car_auctions  # noqa: F401
    import app.scrapers.morris_leslie  # noqa: F401
    import app.scrapers.manor_park  # noqa: F401
    import app.scrapers.porsche_911uk  # noqa: F401
    import app.scrapers.bmw_car_club_gb  # noqa: F401
    import app.scrapers.charterhouse  # noqa: F401
    import app.scrapers.gumtree  # noqa: F401
    import app.scrapers.pistonheads  # noqa: F401
    from app.jobs.scrape_jobs import run_scraper

    source_name = sys.argv[1]
    print(f"Scraping '{source_name}' from this machine, writing to production DB...")
    asyncio.run(run_scraper(source_name))
    print("Done.")

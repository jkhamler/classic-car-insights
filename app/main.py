import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import dashboard, listings, vehicles, trends, alerts, reports, scraper_admin
from app.api.health import router as health_router
from app.jobs.scheduler import lifespan

# Import scrapers to trigger registration
import app.scrapers.bring_a_trailer  # noqa: F401
import app.scrapers.pistonheads  # noqa: F401
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

app = FastAPI(title="Classic Car Insights", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        os.getenv("RAILWAY_PUBLIC_DOMAIN", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(scraper_admin.router, prefix="/api/admin", tags=["admin"])

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {"status": "ok", "app": "Classic Car Insights"}

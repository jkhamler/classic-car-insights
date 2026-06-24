import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import auction_sales
from app.api.health import router as health_router

app = FastAPI(title="Classic Car Insights")

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

# Health check endpoint
app.include_router(health_router, prefix="/health", tags=["health"])

# API routes — mounted at both /api/auction-sales (for the frontend proxy
# convention) and /auction-sales (for direct access / backwards compat)
app.include_router(
    auction_sales.router,
    prefix="/api/auction-sales",
    tags=["auction-sales"],
)
app.include_router(
    auction_sales.router,
    prefix="/auction-sales",
    tags=["auction-sales"],
)

# Serve the React frontend build if it exists (production)
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
        return {"status": "ok"}

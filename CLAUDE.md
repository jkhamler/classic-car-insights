# CLAUDE.md

## Project Overview

Classic Car Insights is a subscription-ready intelligence platform that finds undervalued modern classics (1990–2015) on niche/obscure sources before they hit mainstream auction platforms. It scrapes multiple data sources, scores listings against benchmark pricing, and uses AI (Claude) to generate actionable insights.

**Core value prop**: Arbitrage detection. Benchmark prices from premium platforms (BaT) vs. discovery on niche sources (classifieds, small auctions, forums). The platform surfaces undervalued cars with explainable scoring.

**Target segment**: Modern classics — European performance (911, M3, M5) + Japanese imports (Skyline, Supra, NSX, Evo, RX-7).

## Commands

### Backend (FastAPI + Poetry)
```bash
poetry install
poetry run uvicorn app.main:app --reload          # Dev server on port 8000
poetry run alembic upgrade head                     # Run migrations
poetry run alembic revision --autogenerate -m "msg" # New migration
```

### Frontend (React + Vite)
```bash
cd classic-car-ui
npm install
npm run dev      # Dev server on port 5173
npm run build    # Type-check + build
npm run lint     # ESLint
```

## Architecture

### Backend (`app/`)
- **FastAPI** app in `app/main.py` with APScheduler lifespan hook
- **Database**: PostgreSQL via SQLAlchemy (sync engine with `psycopg`)
- **Models** (`app/db/models/`): Vehicle, Source, Listing, PriceBenchmark, Alert, AlertMatch, AIReport, ScrapeRun
- **CRUD** (`app/crud/`): One module per model
- **Schemas** (`app/schemas/`): Pydantic models for each domain
- **Scrapers** (`app/scrapers/`): BaseScraper + registry pattern. Implementations: BringATrailer (benchmark), CarAndClassic (discovery), PistonHeads (discovery)
- **Services** (`app/services/`): scoring.py (undervaluation engine), benchmark_calculator.py, vehicle_matcher.py, ai_analysis.py (Claude API), seed.py
- **Jobs** (`app/jobs/`): APScheduler-based background jobs for scraping, scoring, benchmarks
- **Prompts** (`app/prompts/`): Text templates for AI analysis
- **Config**: `app/core/config.py` uses pydantic-settings. Required: `DATABASE_URL`. Optional: `ANTHROPIC_API_KEY`, `OLD_CARS_DATA_API_KEY`

### Frontend (`classic-car-ui/`)
- **React 19 + TypeScript + Vite + Tailwind CSS v4**
- **React Router** for client-side routing, **TanStack Query** for data fetching
- **Pages**: Dashboard, Listings (search/filter), ListingDetail (score breakdown + AI), Vehicles, VehicleDetail (price chart + thesis), Trends, Alerts, Reports
- **Vite proxy**: `/api` requests proxied to `http://localhost:8000` (no rewrite — backend routes include `/api`)

### Key API Endpoints (all under `/api/`)
- `GET /dashboard/stats` — Dashboard KPIs
- `GET /dashboard/top-opportunities` — Highest-scoring active listings
- `GET /listings` — Search/filter with pagination
- `GET /listings/{id}` — Full detail with score breakdown
- `GET /vehicles` — Tracked vehicles with benchmark prices
- `GET /vehicles/{id}/price-history` — Time series for charting
- `GET /trends/movers` — Biggest price movers
- CRUD on `/alerts`
- `GET /reports/weekly` — AI-generated weekly digest
- `POST /admin/scrape/{source_name}` — Trigger scraper manually
- `POST /admin/score/refresh` — Re-score all active listings
- `POST /admin/benchmarks/recalculate` — Recompute benchmarks

### Scoring Engine
Weighted composite score (0–100): price vs benchmark (40%), mileage (15%), market trend (15%), scarcity (15%), freshness (10%), source quality (5%). Deterministic + explainable.

## Environment
- Python 3.11, Poetry v2
- Node.js (for frontend)
- PostgreSQL (Railway)
- `.env` requires: `DATABASE_URL`, optionally `ANTHROPIC_API_KEY`
- Deployed on Railway with multi-stage Dockerfile

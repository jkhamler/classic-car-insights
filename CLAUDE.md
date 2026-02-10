# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classic Car Insights is a full-stack application for tracking and analyzing classic car auction prices. It ingests auction data from an external API ("Old Cars Data API"), stores it in PostgreSQL, and displays price trend charts in a React dashboard.

## Commands

### Backend (FastAPI + Poetry)
```bash
# Install dependencies
poetry install

# Run the API server (default port 8000)
poetry run uvicorn app.main:app --reload

# Run Alembic migrations
poetry run alembic upgrade head

# Generate a new migration
poetry run alembic revision --autogenerate -m "description"
```

### Frontend (React + Vite)
```bash
cd classic-car-ui
npm install
npm run dev      # Dev server on port 5173
npm run build    # Type-check then build
npm run lint     # ESLint
```

## Architecture

### Backend (`app/`)
- **FastAPI** app defined in `app/main.py`. Routes are mounted under `/auction-sales` and `/health`.
- **Database**: PostgreSQL via SQLAlchemy (sync engine with `psycopg`). Session factory and `get_db` dependency in `app/db/session.py`. Declarative base in `app/db/base.py`.
- **Single model**: `AuctionSale` in `app/db/models/auction_sale.py` — uses `public` schema explicitly.
- **CRUD layer**: `app/crud/auction_sales.py` — includes price trend aggregation (grouped by make + year-month) and filter options (distinct makes/models/years).
- **Schemas**: Pydantic models in `app/schemas/auction_sale.py` — `AuctionSaleCreate`, `AuctionSaleRead`, `PriceTrendResponse`, `FilterOptions`, `ImportResponse`.
- **External API**: `app/services/old_cars_api.py` calls the Old Cars Data API (Bearer token auth). `app/services/populate_db.py` orchestrates fetching and inserting records via the `/auction-sales/import` endpoint.
- **Config**: `app/core/config.py` uses `pydantic-settings` to load from `.env`. Required: `DATABASE_URL`. Optional: `OLD_CARS_DATA_API_KEY`, `OLD_CARS_BASE_URL`.
- **Migrations**: Alembic in `alembic/`. The `alembic/env.py` manually loads `.env` and imports all models to register them with `Base.metadata`.

### Frontend (`classic-car-ui/`)
- **React 19 + TypeScript + Vite**. Styling via **Tailwind CSS v4** (using `@tailwindcss/vite` plugin).
- **Vite proxy**: `/api` requests are proxied to `http://localhost:8000` with the `/api` prefix stripped. Frontend API calls use `/api/auction-sales/...` paths (see `src/services/api.ts`).
- **Components**: `FilterPanel` (make/model/year selectors), `PriceTrendChart` (Recharts line chart).
- **Charts**: Uses **Recharts** library for data visualization.
- **Types**: TypeScript interfaces in `src/types/auction.ts` mirror the backend Pydantic schemas.

### Key API Endpoints
- `GET /auction-sales` — paginated list
- `POST /auction-sales` — create single record
- `POST /auction-sales/import?make=...` — bulk import from external API
- `GET /auction-sales/trends?make=...` — aggregated price trends
- `GET /auction-sales/filters` — available filter values

## Environment Setup

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` — PostgreSQL connection string (format: `postgresql+psycopg://user:pass@host/db`)
- `OLD_CARS_DATA_API_KEY` — API key for the external auction data service
- `OLD_CARS_BASE_URL` — Base URL for the external auction data service

Python version: 3.11 (see `.python-version`). Package management: Poetry (v2).

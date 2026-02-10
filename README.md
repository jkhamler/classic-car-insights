# Classic Car Insights

A full-stack application for tracking and analyzing classic car auction prices. Import auction data from external sources, store it in PostgreSQL, and explore price trends through an interactive dashboard.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Recharts
- **Package Management**: Poetry (backend), npm (frontend)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js
- PostgreSQL
- Poetry

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jkhamler/classic-car-insights.git
   cd classic-car-insights
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Fill in your `.env`:
   - `DATABASE_URL` — PostgreSQL connection string (`postgresql+psycopg://user:pass@host/db`)
   - `OLD_CARS_DATA_API_KEY` — API key for the external auction data service
   - `OLD_CARS_BASE_URL` — Base URL for the external auction data service

3. **Install backend dependencies**
   ```bash
   poetry install
   ```

4. **Run database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

5. **Install frontend dependencies**
   ```bash
   cd classic-car-ui
   npm install
   ```

### Running the App

Start the backend and frontend in separate terminals:

```bash
# Backend (port 8000)
poetry run uvicorn app.main:app --reload

# Frontend (port 5173)
cd classic-car-ui
npm run dev
```

The frontend dev server proxies `/api` requests to the backend automatically.

Open [http://localhost:5173](http://localhost:5173) to use the dashboard.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auction-sales` | List auction sales (paginated) |
| `POST` | `/auction-sales` | Create a single auction sale |
| `POST` | `/auction-sales/import?make=...` | Bulk import from external API |
| `GET` | `/auction-sales/trends?make=...` | Aggregated price trends by make |
| `GET` | `/auction-sales/filters` | Available filter values (makes, models, years) |
| `GET` | `/health` | Health check |

Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

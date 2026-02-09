from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auction_sales
from app.api.health import router as health_router

app = FastAPI(title="Classic Car Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
app.include_router(health_router, prefix="/health", tags=["health"])

# Root endpoint
@app.get("/")
def root():
    return {"status": "ok"}

# Auction sales endpoints
app.include_router(
    auction_sales.router,
    prefix="/auction-sales",  # Use hyphen for consistency in URL
    tags=["auction-sales"]
)

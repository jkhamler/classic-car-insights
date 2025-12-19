from fastapi import FastAPI
from app.api import auction_sales
from app.api.health import router as health_router

app = FastAPI(title="Classic Car Insights")

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

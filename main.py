from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(title="Classic Auction Watchlist")

app.include_router(health_router)


@app.get("/")
def root():
    return {"status": "ok"}

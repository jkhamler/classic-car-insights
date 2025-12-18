from fastapi import FastAPI
from app.api import auction_sales
from app.api.health import router as health_router

app = FastAPI(title="Classic Car Insights")

app.include_router(health_router)


@app.get("/")
def root():
    return {"status": "ok"}


app.include_router(
    auction_sales.router,
    prefix="/auction_sales",
    tags=["auction_sales"]
)

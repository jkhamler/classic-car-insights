import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OLD_CARS_API_KEY")
BASE_URL = os.getenv("OLD_CARS_BASE_URL")


def fetch_auction_sales(make: str, model: str | None = None, limit: int = 20):
    if not make:
        raise ValueError("`make` parameter is required for this API call")

    params = {"make": make, "limit": limit}
    if model:
        params["model"] = model

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/auctions", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Classic Auction Watchlist"
    database_url: str = "postgresql+psycopg://localhost/auction_watchlist"
    old_cars_data_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()

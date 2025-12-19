from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    old_cars_data_api_key: str | None = None  # <-- optional
    old_cars_base_url: str | None = None

    class Config:
        env_file = ".env"
        extra = "allow"
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str | None = None
    old_cars_data_api_key: str | None = None
    old_cars_base_url: str | None = None

    scraper_user_agent: str = "ClassicCarInsights/1.0"
    scraper_default_rate_limit: float = 2.0
    min_score_for_ai_analysis: int = 60
    enable_scheduler: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"

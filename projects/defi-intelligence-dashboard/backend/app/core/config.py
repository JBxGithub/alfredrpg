from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "DeFi Intelligence Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SERVER_PORT: int = 8100

    DATABASE_URL: str = "sqlite+aiosqlite:///./defi_dashboard.db"

    DEFILAMA_API_BASE: str = "https://api.llama.fi"
    DEFILAMA_API_TIMEOUT: int = 30

    ACLED_API_BASE: str = "https://api.acleddata.com"
    GDELT_API_BASE: str = "https://api.gdeltproject.org"
    USGS_API_BASE: str = "https://earthquake.usgs.gov/fdsnws/event/1"
    WEATHER_API_BASE: str = "https://api.openweathermap.org/data/2.5"

    WORLD_DATA_CACHE_TTL: int = 3600

    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()

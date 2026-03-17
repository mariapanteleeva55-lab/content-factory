from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    assemblyai_api_key: str = ""
    twelve_labs_api_key: str = ""

    # Video Generation APIs
    heygen_api_key: str = ""
    elevenlabs_api_key: str = ""
    runway_api_key: str = ""

    # Discovery APIs
    youtube_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ContentFactory/1.0"
    apify_api_key: str = ""

    # Storage
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Queue
    redis_url: str = "redis://localhost:6379/0"

    # App
    debug: bool = False
    download_dir: str = "./downloads"
    output_dir: str = "./outputs"

    # Niche config
    niche_name: str = "уходовая косметика Марья"
    niche_audience: str = "женщины 18-45 лет, интересующиеся уходом за кожей, натуральной косметикой и beauty-ритуалами"
    brand_name: str = "Марья"
    brand_tone: str = "тёплый, экспертный, без давления, вдохновляющий"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

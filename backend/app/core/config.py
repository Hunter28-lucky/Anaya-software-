import os
import base64
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "LeadQualify AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./leadqualify.db",
        description="Async SQLAlchemy database URL (SQLite or PostgreSQL/Supabase)"
    )

    # Supabase / Auth
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SECRET_KEY: str = "leadqualify-dev-secret-key-change-in-production-12345"

    # OpenRouter AI
    OPENROUTER_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY") or (
            base64.b64decode(
                b"c2stb3ItdjEtYzJkNmVjZWMxZGMzODcxMmI5ZWMwNWIxZTIyYTU2MWQ3YTI5Y2VhZTdmZTFlNjQzNWU3ZTcwYmZhNDNlYzM2YQ=="
            ).decode("utf-8")
        ),
        description="Secret OpenRouter API key"
    )
    OPENROUTER_MODEL: str = Field(
        default="nvidia/nemotron-3.5-lightning:free",
        description="OpenRouter model identifier"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API Base URL"
    )

    # Crawler Settings (Optimized for High Speed & Trustworthy Coverage)
    CRAWLER_MAX_PAGES_PER_DOMAIN: int = 3
    CRAWLER_MAX_DEPTH: int = 2
    CRAWLER_TIMEOUT_SECONDS: float = 6.0
    CRAWLER_MAX_CONTENT_BYTES: int = 5 * 1024 * 1024  # 5 MB
    CRAWLER_PER_DOMAIN_DELAY: float = 0.05  # seconds
    CRAWLER_USER_AGENT: str = "LeadQualifyAI-Verifier/1.0 (+https://leadqualify.ai/bot)"
    CRAWLER_CONCURRENCY: int = 8

    # Security
    BLOCKED_IPS_AND_RANGES: List[str] = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "0.0.0.0/8",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    ]
    ALLOWED_PORTS: List[int] = [80, 443, 8080, 8443]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8008",
        "http://127.0.0.1:8008",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


settings = Settings()

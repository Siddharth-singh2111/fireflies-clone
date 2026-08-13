"""Application configuration, driven entirely by environment variables.

Keeping config in one typed place (Pydantic Settings) means the app is
deployment-agnostic: the same code runs locally and on Render/Railway/Docker,
only the env values change. Nothing here hard-codes a host or a secret.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    app_name: str = "Fireflies Clone API"
    # SQLite by default. On a host with a persistent disk, point this at the
    # mounted volume, e.g. sqlite:////data/app.db
    database_url: str = "sqlite:///./fireflies.db"

    # Comma-separated list of allowed frontend origins for CORS.
    cors_origins: str = "http://localhost:3000"

    # Load demo data automatically on startup if the database is empty.
    # Safe with a persistent disk (only seeds an empty DB); keeps the demo
    # populated on ephemeral free-tier hosts that reset the filesystem.
    auto_seed: bool = True

    # --- Uploads ---
    max_upload_bytes: int = 5 * 1024 * 1024  # 5 MB cap on transcript files

    # --- Optional LLM (hybrid mode) ---
    # If a key is present we can call a real LLM for "regenerate summary" and
    # "ask this meeting". If absent, the app falls back to a deterministic
    # extractive engine so the demo never breaks. No key is required to run.
    llm_provider: str = "none"          # "anthropic" | "openai" | "none"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()

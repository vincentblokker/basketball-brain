from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenRouter — single gateway for Claude/GPT/Gemini, OpenAI-compatible API
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://brain.clubduty.app"
    openrouter_site_name: str = "Basketball Brain"

    chroma_persist_dir: str = "./chroma"
    embedding_model: str = "BAAI/bge-m3"
    # OpenRouter-style model IDs: <provider>/<model>
    # Default Haiku — ~10× cheaper than Sonnet, quality is fine for grounded
    # RAG answers. Override via LLM_MODEL env var when needed.
    llm_model: str = "anthropic/claude-haiku-4-5"
    cr_model: str = "anthropic/claude-haiku-4-5"
    default_tenant: str = "public"
    log_level: str = "INFO"

    # Admin upload UI — bearer token check on /admin/* endpoints.
    # Generate a random one with: openssl rand -hex 32
    admin_token: str = ""
    raw_dir: str = "./data/raw"

    # Rate-limit on /query — per-IP, rolling window. Set to 0 to disable.
    # Defaults are generous for trusted users but block scraper abuse.
    rate_limit_per_day: int = 20
    rate_limit_per_hour: int = 10
    # Trust X-Forwarded-For when behind a reverse proxy (Caddy on host).
    rate_limit_trust_forwarded: bool = True

    # Metrics SQLite — query log + eval-run log for the admin dashboard.
    metrics_db_path: str = "./data/metrics/metrics.sqlite"


settings = Settings()

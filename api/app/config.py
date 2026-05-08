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
    llm_model: str = "anthropic/claude-sonnet-4-6"
    cr_model: str = "anthropic/claude-haiku-4-5"
    default_tenant: str = "public"
    log_level: str = "INFO"

    # Admin upload UI — bearer token check on /admin/* endpoints.
    # Generate a random one with: openssl rand -hex 32
    admin_token: str = ""
    raw_dir: str = "./data/raw"


settings = Settings()

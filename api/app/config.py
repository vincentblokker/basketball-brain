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

    # Demo / cost guard — when true, /query runs retrieval as normal but SKIPS
    # the paid OpenRouter generation call, returning the real citations plus
    # `demo_notice` as the answer text. Keeps a public demo free to run. Toggle
    # via the QUERY_GENERATION_DISABLED env var (recreate the container to apply).
    query_generation_disabled: bool = False
    demo_notice: str = (
        "Live antwoorden staan even uit om de hostingkosten te beperken nu deze "
        "demo publiek staat. De bronnen hieronder zijn wél echt opgehaald uit de "
        "officiële documenten — dat retrieval-gedeelte is de kern van Basketball "
        "Brain. (Live answers are temporarily paused to cap hosting costs; the "
        "sources below are still retrieved for real.)"
    )

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

    # Hybrid-retrieval defaults — the tuned "Final Configuration" from the
    # evaluation report (docs/eval-report.md): dense-heavy 2:1 weighting,
    # top_k=5. /query reads these so production runs the tuned config; override
    # per env (VECTOR_WEIGHT / KEYWORD_WEIGHT / TOP_K), no re-ingest needed.
    vector_weight: float = 2.0
    keyword_weight: float = 1.0
    top_k: int = 5

    # Static-file dir for rendered PDF page thumbnails. The relative default
    # resolves to /app/data/pages in the container (WORKDIR=/app, the bind-mount
    # target) and to api/data/pages locally. Override with PAGES_DIR if needed.
    pages_dir: str = "./data/pages"


settings = Settings()

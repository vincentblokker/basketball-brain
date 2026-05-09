from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import admin as admin_router
from app.routers import eval as eval_router
from app.routers import metrics as metrics_router
from app.routers import query as query_router

app = FastAPI(title="Basketball Brain API", version="0.1.0")

# Rate-limit must run BEFORE CORS so the 429 still gets CORS headers.
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://brain.clubduty.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Limit-Day",
        "X-RateLimit-Remaining-Day",
        "X-RateLimit-Limit-Hour",
        "X-RateLimit-Remaining-Hour",
        "Retry-After",
    ],
)

app.include_router(query_router.router)
app.include_router(eval_router.router)
app.include_router(admin_router.router)
app.include_router(metrics_router.router)

# Serve per-page PDF screenshots. Caddy strips /api/ so external URL is
# /api/pages/{source_id}/page-NNNN.png which lands here as /pages/...
_pages_dir = Path("/app/data/pages")
_pages_dir.mkdir(parents=True, exist_ok=True)
app.mount("/pages", StaticFiles(directory=str(_pages_dir)), name="pages")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

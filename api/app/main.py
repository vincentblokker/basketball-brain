from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin as admin_router
from app.routers import eval as eval_router
from app.routers import query as query_router

app = FastAPI(title="Basketball Brain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://brain.clubduty.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(query_router.router)
app.include_router(eval_router.router)
app.include_router(admin_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

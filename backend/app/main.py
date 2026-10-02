from fastapi import FastAPI

from app.api import router as api_router

app = FastAPI(
    title="LearnLens API",
    version="0.1.0",
    description="Study assistant API. This version exposes a health check only.",
)

app.include_router(api_router)

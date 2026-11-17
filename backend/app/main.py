# FastAPI app entry point. Server start aagum bodhu idhu dhaan mudhalla run aagum.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import face, health, qr
from app.config import APP_NAME, APP_VERSION, CORS_ORIGIN_REGEX, TMP_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Server start: tmp folder irukka nu confirm pannrom
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Server stop: (cleanup logic pinnadi serkkalam)


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Frontend (localhost:3000) backend-a call panna CORS allow
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(face.router)
app.include_router(qr.router)


@app.get("/")
def root():
    return {"message": f"{APP_NAME} run aagudhu", "docs": "/docs", "health": "/health"}
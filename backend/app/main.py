import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registers tables)
from app.config import settings
from app.database import Base, engine
from app.routes import dashboard, incidents, risk, vision
from app.services import jobs

logging.basicConfig(level=logging.INFO)

settings.ensure_dirs()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    jobs.recover_stuck_jobs()
    yield


app = FastAPI(title="NirmaanAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(vision.router)
app.include_router(incidents.router)
app.include_router(risk.router)
app.include_router(dashboard.router)
app.mount("/media/snapshots", StaticFiles(directory=settings.snapshot_dir), name="snapshots")


@app.get("/api/health")
def health():
    return {"status": "ok"}

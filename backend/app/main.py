from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import router
from .scheduler import start_scheduler, stop_scheduler


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Douyin Itinerary",
    description=(
        "Extracts date + place itineraries from the bios of followed Douyin "
        "creators. See https://github.com/Ami11111/douyin-itinerary"
    ),
    version="0.1.0",
    license_info={
        "name": "MIT",
        "url": "https://github.com/Ami11111/douyin-itinerary/blob/main/LICENSE",
    },
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import router
from .config import Settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

app = FastAPI(
    lifespan=lifespan,
    debug=Settings().debug,
    title=Settings().title,
    version=Settings().version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings().origins,
    allow_credentials=Settings().allow_credentials,
    allow_methods=Settings().allow_methods,
    allow_headers=Settings().allow_headers,
)

app.include_router(router)

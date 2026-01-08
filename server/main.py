from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from server.routes import router
from server.config import Settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

app = FastAPI(
    lifespan=lifespan,
    debug=Settings().debug,
    title=Settings().app_name,
    version=Settings().app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings().cors_allowed_origins,
    allow_credentials=Settings().cors_allow_credentials,
    allow_methods=Settings().cors_allowed_methods,
    allow_headers=Settings().cors_allowed_headers,
)

app.include_router(router)

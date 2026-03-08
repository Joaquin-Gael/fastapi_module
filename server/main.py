from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from server.config import Settings
from server.core.database import close_db, init_db
from server.core.utils.logger import get_logger
from server.routes import router

console = Console()
logger = get_logger(__name__)

panel = Panel(Text(f"{Settings().server_domain}{Settings().scalar_url}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan startup: Initializing DB...")
    await init_db()
    logger.info("Lifespan startup: DB Initialized.")
    console.print(panel)
    yield
    logger.info("Lifespan shutdown: Closing DB...")
    await close_db()
    logger.info("Lifespan shutdown: DB Closed.")


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

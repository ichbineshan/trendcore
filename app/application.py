from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import loaded_config
from config.sentry import configure_sentry
from app.router import api_router
from utils.load_config import run_on_startup, run_on_exit


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_on_startup()
    yield
    await run_on_exit()


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of the application.

    Returns:
        FastAPI application instance
    """
    # Enable sentry integration if configured
    configure_sentry()

    app = FastAPI(
        debug=loaded_config.debug,
        title="Trend Analysis",
        description="AI-powered trend analysis with single agent chat",
        version="1.0.0",
        docs_url="/api-reference",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        root_path="/",
    )

    # CORS configuration
    allowed_origins = ["*"] if loaded_config.env == "local" else []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router)

    return app

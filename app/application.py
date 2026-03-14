from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# from app.middleware import (
#     validation_exception_handler,
#     generic_validation_exception_handler,
#     http_exception_handler,
#     generic_exception_handler
# )

from config.settings import loaded_config
from utils.load_config import run_on_startup, run_on_exit


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_on_startup()
    yield
    await run_on_exit()



async def healthz():
    return JSONResponse(status_code=200, content={"success": True})


def get_app():
    base_app = FastAPI(
        debug=False,
        title="Night Eye API",
        description="AI-powered brand identity and trend analysis platform",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    base_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Only allow this origins
        # allow_origins=[],  # Only allow this origins
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )



    api_router_healthz = APIRouter()
    api_router_healthz.add_api_route(
        "/_healthz", methods=["GET"], endpoint=healthz, include_in_schema=False
    )
    api_router_healthz.add_api_route(
        "/_readyz", methods=["GET"], endpoint=healthz, include_in_schema=False
    )

    base_app.include_router(api_router_healthz)

    if loaded_config.server_type == "night_eye":
        from brand.routes import router as brand_router
        from collection.routes import router as collection_router
        from themes.routes import router as themes_router

        api_router_v1 = APIRouter(prefix="/v1.0")
        api_router_v1.include_router(brand_router)
        api_router_v1.include_router(collection_router)
        api_router_v1.include_router(themes_router)


        base_app.include_router(api_router_v1)



    return base_app
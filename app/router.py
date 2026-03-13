from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from streaming.routes import streaming_router
from agents.router import router as collection_brief_router


async def healthz():
    """Health check endpoint."""
    return JSONResponse(status_code=200, content={"status": "ok"})


api_router = APIRouter()

# Version 1.0 routes
api_router_v1 = APIRouter(prefix="/v1.0")
api_router_v1.include_router(streaming_router)
api_router_v1.include_router(collection_brief_router)

# Health check
api_router_healthz = APIRouter()
api_router_healthz.add_api_route(
    "/_healthz", methods=["GET"], endpoint=healthz, include_in_schema=False
)

api_router.include_router(api_router_healthz)
api_router.include_router(api_router_v1)

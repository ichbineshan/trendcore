import uvicorn
import uvloop
import asyncio

from config.settings import loaded_config


def main() -> None:
    """Entrypoint of the application."""
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    uvicorn.run(
        "app.application:get_app",
        workers=loaded_config.workers_count,
        host=loaded_config.host,
        port=loaded_config.port,
        reload=loaded_config.debug,
        loop="uvloop",
        factory=True,
    )

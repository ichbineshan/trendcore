import os

from config.settings import loaded_config
from utils.temporal.worker_registry import list_worker_names
import sys

# Import all worker modules to register them with the worker registry
# The @register_worker decorator runs at import time
import brand.temporal.workers  # noqa: F401
import collection.temporal.workers  # noqa: F401
import themes.temporal.workers  # noqa: F401
import trend.temporal.workers  # noqa: F401
import moodboard.temporal.workers  # noqa: F401
import styles.temporal.workers  # noqa: F401

if loaded_config.env == "local":
    os.environ.setdefault('PKG_CONFIG_PATH', '/opt/homebrew/lib/pkgconfig:/opt/homebrew/opt/libffi/lib/pkgconfig')
    os.environ.setdefault('DYLD_LIBRARY_PATH', '/opt/homebrew/lib')
    os.environ.setdefault('LD_LIBRARY_PATH', '/opt/homebrew/lib')

if loaded_config.mode == "server":
    from app.main import main as server_main

    if __name__ == "__main__":
        server_main()


elif loaded_config.mode in list_worker_names():
    try:
        import asyncio
        from utils.temporal.health import run_worker

        print("Starting Temporal Worker")
        asyncio.run(run_worker(loaded_config.mode))
    except Exception as e:
        print(f"ENTRYPOINT: Error message: {e}", file=sys.stderr, flush=True)
        print("ENTRYPOINT: Full traceback:", file=sys.stderr, flush=True)
else:
    print(f"ENTRYPOINT: Unknown mode '{loaded_config.mode}'", file=sys.stderr, flush=True)



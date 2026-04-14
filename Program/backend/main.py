import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .clients import lta as lta_client
from .clients.nea import get_2hr_forecast
from dotenv import load_dotenv


def _warm_cache():
    """Pre-fetch lightweight datasets only. Heavy paginated datasets
    (speed bands, carparks) are fetched on-demand with per-key locks
    to avoid duplicate work — this keeps startup memory low."""
    print("[STARTUP] Warming cache: bus_stops, weather...")
    try:
        lta_client.get_bus_stops()
    except Exception as e:
        print(f"[STARTUP] bus_stops warm failed: {e}")
    try:
        get_2hr_forecast()
    except Exception as e:
        print(f"[STARTUP] weather warm failed: {e}")
    print("[STARTUP] Cache warm complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm lightweight caches in background — don't block startup
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _warm_cache)
    yield


def create_app() -> FastAPI:
    # Load .env once at startup so root-level modules also see env vars
    load_dotenv()
    app = FastAPI(title="SGTravelBud Backend", version="0.1.0", lifespan=lifespan)

    # Allow local dev frontends to call the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(api_router)
    return app


app = create_app()

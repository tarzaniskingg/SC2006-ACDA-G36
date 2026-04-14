import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .clients import lta as lta_client
from .clients.nea import get_2hr_forecast
from dotenv import load_dotenv


def _warm_cache():
    """Pre-fetch heavy paginated datasets so user requests never wait."""
    print("[STARTUP] Warming cache: bus_stops, traffic_speed_bands, carpark, weather...")
    try:
        lta_client.get_bus_stops()
    except Exception as e:
        print(f"[STARTUP] bus_stops warm failed: {e}")
    try:
        lta_client.get_traffic_speed_bands()
    except Exception as e:
        print(f"[STARTUP] traffic_speed_bands warm failed: {e}")
    try:
        lta_client.get_carpark_availability()
    except Exception as e:
        print(f"[STARTUP] carpark warm failed: {e}")
    try:
        get_2hr_forecast()
    except Exception as e:
        print(f"[STARTUP] weather warm failed: {e}")
    print("[STARTUP] Cache warm complete.")


_refresh_stop = threading.Event()


def _background_refresh():
    """Periodically refresh heavy datasets before TTL expires."""
    while not _refresh_stop.is_set():
        _refresh_stop.wait(240)  # refresh every 4 min (TTL is 5 min)
        if _refresh_stop.is_set():
            break
        print("[REFRESH] Background cache refresh...")
        _warm_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm cache BEFORE accepting requests — this ensures the first
    # user request hits warm data instead of triggering slow paginated fetches
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warm_cache)
    # Start background refresh thread to keep cache warm
    _refresh_stop.clear()
    t = threading.Thread(target=_background_refresh, daemon=True)
    t.start()
    yield
    _refresh_stop.set()


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

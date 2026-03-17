from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from dotenv import load_dotenv


def create_app() -> FastAPI:
    # Load .env once at startup so root-level modules also see env vars
    load_dotenv()
    app = FastAPI(title="SGTravelBud Backend", version="0.1.0")

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

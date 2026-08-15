import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.datasets import router as datasets_router
from api.routes.health import router as health_router
from services.dataset_service import DatasetService
from services.query_service import QueryService
from services.session_registry import SessionRegistry


def create_app(runtime_root: str | None = None) -> FastAPI:
    app = FastAPI(title="Data Assistant API", version="0.1.0")
    origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    registry = SessionRegistry(
        runtime_root or os.getenv("RUNTIME_ROOT", ".runtime/datasets")
    )
    app.state.registry = registry
    app.state.dataset_service = DatasetService(registry)
    app.state.query_service = QueryService(registry)
    app.include_router(health_router)
    app.include_router(datasets_router)
    return app


app = create_app()

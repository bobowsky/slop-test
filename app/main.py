from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR, UPLOADS_DIR, VRESC_CONTENT_DIR
from app.routers import generate, health, hint, scene, vapi


def _create_app() -> FastAPI:
    app = FastAPI(title="Room2Learn", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(generate.router)
    app.include_router(hint.router)
    app.include_router(health.router)
    app.include_router(scene.router)
    app.include_router(vapi.router)

    _wire_services(app)

    @app.get("/", response_class=FileResponse, include_in_schema=False)
    async def serve_landing_page() -> FileResponse:
        return FileResponse(path=str(STATIC_DIR / "index.html"))

    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
    app.mount("/content", StaticFiles(directory=str(VRESC_CONTENT_DIR), check_dir=False), name="content")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def _wire_services(app: FastAPI) -> None:
    """Inject services that are still routed through dependency overrides."""

    # Hint endpoint remains provider-based. Keep mock provider as the default
    # in both modes until a dedicated real implementation lands.
    from app.services.mock_hint import MockHintProvider

    hint_provider = MockHintProvider()
    app.dependency_overrides[hint._get_hint_provider] = lambda: hint_provider


app = _create_app()

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers, unhandled_error_handler
from app.api.routes import health, notifications, operators, tickets
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = FastAPI(title="Maintenance Tickets API", docs_url="/docs")

    @app.middleware("http")
    async def catch_unhandled(request: Request, call_next):
        # Registered before CORSMiddleware, so it sits inside it and 500
        # responses still get CORS headers.
        try:
            return await call_next(request)
        except Exception as exc:
            return await unhandled_error_handler(request, exc)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    for module in (health, tickets, operators, notifications):
        app.include_router(module.router)
    return app


app = create_app()

# app/utils/exception_handlers.py

"""
Registers handlers that convert our domain exceptions into HTTP responses.
Routers/services just raise NotFoundError, OwnershipError, etc. — they
never need to know what HTTP status code that maps to.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleError,
    OwnershipError,
    ExternalServiceError,
    BungeWatchError,
)

logger = logging.getLogger("bungewatch")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ResourceAlreadyExistsError)
    async def handle_duplicate(request: Request, exc: ResourceAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(OwnershipError)
    async def handle_ownership(request: Request, exc: OwnershipError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(BusinessRuleError)
    async def handle_business_rule(request: Request, exc: BusinessRuleError):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(ExternalServiceError)
    async def handle_external_service(request: Request, exc: ExternalServiceError):
        # Log the FULL debug context (internal) but never expose it to the client.
        logger.error(f"External service failure: {exc.message}", extra=exc.debug_context)
        return JSONResponse(
            status_code=502,
            content={"detail": f"{exc.service_name} is currently unavailable. Please try again shortly."},
        )

    # Catch-all for any OTHER BungeWatchError subclass not handled above —
    # still a KNOWN error type, just not one with a specific status mapping yet.
    @app.exception_handler(BungeWatchError)
    async def handle_generic_app_error(request: Request, exc: BungeWatchError):
        logger.warning(f"Unhandled BungeWatchError subtype: {type(exc).__name__}: {exc.message}")
        return JSONResponse(status_code=400, content={"detail": exc.message})
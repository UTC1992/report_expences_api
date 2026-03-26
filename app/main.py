from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.error_capture import capture_exception
from app.core.exceptions import DuplicateResourceError, NotFoundError, ValidationError
from app.core.logging_config import configure_logging
from app.core.problem_details import (
    TYPE_CONFLICT,
    TYPE_INTERNAL,
    TYPE_NOT_FOUND,
    TYPE_REQUEST_VALIDATION,
    TYPE_VALIDATION,
    problem_json_response,
)
from app.modules.expenses.api.routes import chat_router, expenses_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(title=settings.app_name, debug=settings.debug)

    @application.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        capture_exception(exc, request, expected=True)
        return problem_json_response(
            request,
            status=404,
            title="Resource not found",
            detail=str(exc),
            type_uri=TYPE_NOT_FOUND,
        )

    @application.exception_handler(ValidationError)
    async def _domain_validation(request: Request, exc: ValidationError) -> JSONResponse:
        capture_exception(exc, request, expected=True)
        return problem_json_response(
            request,
            status=422,
            title="Validation failed",
            detail=str(exc),
            type_uri=TYPE_VALIDATION,
        )

    @application.exception_handler(DuplicateResourceError)
    async def _duplicate(request: Request, exc: DuplicateResourceError) -> JSONResponse:
        capture_exception(exc, request, expected=True)
        return problem_json_response(
            request,
            status=409,
            title="Duplicate resource",
            detail=str(exc),
            type_uri=TYPE_CONFLICT,
        )

    @application.exception_handler(RequestValidationError)
    async def _request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        capture_exception(
            exc,
            request,
            expected=True,
            extra={"errors": exc.errors()},
        )
        return problem_json_response(
            request,
            status=422,
            title="Request validation failed",
            detail="The request body or query parameters are invalid.",
            type_uri=TYPE_REQUEST_VALIDATION,
            extensions={"errors": exc.errors()},
        )

    @application.exception_handler(HTTPException)
    async def _http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        expected = exc.status_code < 500
        capture_exception(exc, request, expected=expected)
        detail_str = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return problem_json_response(
            request,
            status=exc.status_code,
            title=_http_error_title(exc.status_code),
            detail=detail_str,
            type_uri="about:blank",
        )

    @application.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        capture_exception(exc, request, expected=False)
        detail = str(exc) if settings.debug else "An unexpected error occurred."
        return problem_json_response(
            request,
            status=500,
            title="Internal server error",
            detail=detail,
            type_uri=TYPE_INTERNAL,
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(chat_router, prefix=f"{settings.api_prefix}/chat")
    application.include_router(expenses_router, prefix=f"{settings.api_prefix}/expenses")

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


def _http_error_title(status_code: int) -> str:
    return {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        409: "Conflict",
        422: "Unprocessable entity",
        500: "Internal server error",
    }.get(status_code, "HTTP error")


app = create_app()

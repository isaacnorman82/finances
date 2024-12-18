import logging
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from backend.rest_api import get_api_router
from backend.rest_api.metadata import API_VERSION

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s:%(lineno)d -  %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("ofxtools").setLevel(logging.ERROR)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


def _configure_app() -> FastAPI:
    version = f"v{API_VERSION}"

    tags_metadata = [
        {
            "name": "Accounts",
            "description": "",
        },
        {
            "name": "Balance",
            "description": "",
        },
        {
            "name": "Data Series",
            "description": "",
        },
        {
            "name": "Metadata",
            "description": "",
        },
    ]

    app = FastAPI(
        docs_url="/documentation",
        # lifespan=lifespan,
        version=version,
        title="Finances",
        summary="Home Finances Application.",
        contact={
            "name": "Isaac Norman",
            "url": "https://github.com/isaacnorman82/finances",
            "email": "support@hazy.com",
        },
        openapi_tags=tags_metadata,
    )

    app.include_router(get_api_router())

    logger.info(f"CORS: {ALLOWED_ORIGINS=}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    app.add_middleware(LoggingMiddleware)

    return app


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled error: {exc}")
            logger.error(f"Request URL: {request.url}")
            logger.error(f"Request method: {request.method}")
            logger.error(f"Request headers: {request.headers}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise


app = _configure_app()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error occurred: {exc.detail}")
    logger.error(f"Request URL: {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error occurred: {exc.errors()}")
    logger.error(f"Request URL: {request.url}")

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Log the error details
    logger.error(f"Request URL: {request.url}")
    logger.error(f"SQLAlchemy error: {str(exc)}")

    # Return a user-friendly error message
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"An internal server error occurred.  SQLAlchemyError - {exc.__class__.__name__}"
        },
    )


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse(content={"detail": str(e)}, status_code=500)

    return response

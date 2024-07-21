# from contextlib import asynccontextmanager
import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__, db_models
from app.db import create_account_summary_view, engine
from app.rest_api import get_api_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("ofxtools").setLevel(logging.ERROR)

db_models.Base.metadata.create_all(bind=engine)
# create_account_summary_view(engine)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     pass


def _configure_app() -> FastAPI:
    version = f"v{__version__}"

    tags_metadata = [
        {
            "name": "Accounts",
            "description": "View accounts.",
        },
        {
            "name": "Transactions",
            "description": "View transactions.",
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
    app.add_middleware(LoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],  # Allow requests from your Vue app's origin
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

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

# from contextlib import asynccontextmanager
import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__, db_models
from app.db import engine
from app.rest_api import get_api_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

db_models.Base.metadata.create_all(bind=engine)

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
            logger.error(f"Request body: {await request.body()}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise


app = _configure_app()
app.add_middleware(LoggingMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error occurred: {exc.detail}")
    logger.error(f"Request URL: {request.url}")
    # logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error occurred: {exc.errors()}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Body: {await request.body()}")
    # logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# # temp
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}

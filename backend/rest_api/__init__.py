import os

from fastapi import APIRouter

from backend.rest_api.accounts import router as _accounts_router
from backend.rest_api.balance import router as _balance_router
from backend.rest_api.data_series import router as _data_series_router

API_VERSION = "1.0.0"


def get_api_router():
    api_router = APIRouter(prefix="/api")
    api_router.include_router(_accounts_router)
    api_router.include_router(_balance_router)
    api_router.include_router(_data_series_router)

    @api_router.get("/version", summary="List API version", tags=["API"])
    def api_get_version():
        return {"api_version": API_VERSION}

    return api_router

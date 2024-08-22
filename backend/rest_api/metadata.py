import logging

from fastapi import APIRouter

from backend import api_models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metadata", tags=["Metadata"])

API_VERSION = "1.1.0"


@router.get("/version", summary="List API version")
def api_get_version():
    return {"api_version": API_VERSION}


@router.get(
    "/ingest-types/",
    summary="Get the supported ingest types",
)
def api_get_account_balance():
    return [x.value for x in api_models.IngestType]

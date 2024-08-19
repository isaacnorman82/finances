import logging
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend import api_models, crud
from backend.db import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dataseries", tags=["Data Series"])


def keys_list_from_str(keys: Optional[str] = Query(None)) -> Optional[List[int]]:
    if keys is None:
        return None
    return keys.split(",")


@router.get(
    "/",
    summary="Get a set of dated key-value pairs",
    response_model=List[api_models.DataSeries],
)
def api_get_data_seties(
    keys: Optional[List[str]] = Depends(keys_list_from_str),
    # could add date range filter here if needed in future
    db_session: Session = Depends(get_db_session),
):
    return crud.get_data_series(db_session=db_session, keys=keys)


@router.post(
    "/",
    summary="Add data series values.",
    response_model=api_models.AddDataSeriesResult,
)
def api_add_data_series_values(
    values: Union[api_models.DataSeriesCreate, List[api_models.DataSeriesCreate]],
    db_session: Session = Depends(get_db_session),
):
    if not isinstance(values, list):
        values = [values]

    result = crud.create_data_series(db_session=db_session, values=values)

    logger.info(f"Add series result: {result}")
    return result

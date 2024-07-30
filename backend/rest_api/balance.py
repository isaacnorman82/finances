import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from dateutil import parser
from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend import api_models, crud, db_models
from backend.db import get_db_session
from backend.ingest import ingest_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/balance", tags=["Balance"])


def account_ids_list_from_str(account_ids: Optional[str] = Query(None)) -> Optional[List[int]]:
    if account_ids is None:
        return None
    return [int(account_id) for account_id in account_ids.split(",")]


@router.get(
    "/monthly/",
    summary="Get the monthly account balance",
    response_model=List[api_models.MonthlyBalanceResult],
)
def api_get_monthly_account_balance(
    account_ids: Optional[List[int]] = Depends(account_ids_list_from_str),
    db_session: Session = Depends(get_db_session),
):
    return crud.get_monthly_balances(db_session=db_session, account_ids=account_ids)

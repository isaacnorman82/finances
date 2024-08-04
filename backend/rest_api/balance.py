import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend import api_models, crud
from backend.db import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/balance", tags=["Balance"])


def account_id_list_from_str(account_ids: Optional[str] = Query(None)) -> Optional[List[int]]:
    if account_ids is None:
        return None
    return [int(account_id) for account_id in account_ids.split(",")]


@router.get(
    "/monthly/",
    summary="Get the monthly account balance",
    response_model=List[api_models.MonthlyBalanceResult],
)
def api_get_monthly_account_balance(
    account_ids: Optional[List[int]] = Depends(account_id_list_from_str),
    db_session: Session = Depends(get_db_session),
):
    return crud.get_monthly_balances(db_session=db_session, account_ids=account_ids)

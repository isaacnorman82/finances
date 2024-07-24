import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from dateutil import parser
from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

from app import api_models, crud, db_models
from app.db import get_db_session
from app.ingest import ingest_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/balance", tags=["Balance"])


def account_ids_list_from_str(account_ids: Optional[str] = Query(None)) -> Optional[List[int]]:
    if account_ids is None:
        return None
    return [int(account_id) for account_id in account_ids.split(",")]


def parse_year_month(date_str: Optional[str] = None) -> Optional[datetime]:
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format {date_str}, expected YYYY-MM.",
        )


def start_year_month_parser(start_date: Optional[str] = None) -> Optional[datetime]:
    return parse_year_month(start_date)


def end_year_month_parser(end_date: Optional[str] = None) -> Optional[datetime]:
    return parse_year_month(end_date)


@router.get(
    "/monthly/",
    summary="Get the monthly account balance",
    response_model=List[api_models.MonthlyBalanceResult],
)
def api_get_monthly_account_balance(
    account_ids: Optional[List[int]] = Depends(account_ids_list_from_str),
    start_date: Optional[datetime] = Depends(start_year_month_parser),
    end_date: Optional[datetime] = Depends(end_year_month_parser),
    db_session: Session = Depends(get_db_session),
):
    # todo think this doesn't work if there's a gap
    # i.e. there's a transaction in one month, then a month without then more after
    # there should be a monthly balance in between
    logger.info(
        f"monthly balances account_ids: {account_ids}, start_date: {start_date}, end_date: {end_date}"
    )

    return crud.get_monthly_balances(
        db_session=db_session,
        account_ids=account_ids,
        start_date=start_date,
        end_date=end_date,
    )

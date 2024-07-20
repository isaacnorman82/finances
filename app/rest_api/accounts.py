import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from dateutil import parser
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from sqlalchemy.orm import Session

from app import api_models, crud, db_models
from app.db import get_db_session
from app.ingest import ingest_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["Accounts"])


def parse_date(date_str: Optional[str] = None) -> Optional[datetime]:
    if date_str is None:
        return None
    try:
        return parser.parse(date_str, dayfirst=True)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format {date_str}"
        )


def start_date_parser(start_date: Optional[str] = None) -> Optional[datetime]:
    return parse_date(start_date)


def end_date_parser(end_date: Optional[str] = None) -> Optional[datetime]:
    return parse_date(end_date)


def get_account_from_path(
    account_id: int = Path(...), db_session: Session = Depends(get_db_session)
) -> db_models.Account:
    account = crud.get_account(
        account_id=account_id,
        db_session=db_session,
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found"
        )
    return account


# @router.get("", include_in_schema=False)
@router.get("/", summary="List all Accounts", response_model=list[api_models.Account])
def api_get_accounts(
    institution: Optional[str] = None,
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db_session: Session = Depends(get_db_session),
):
    return crud.get_accounts(
        db_session=db_session,
        institution=institution,
        name=name,
        skip=skip,
        limit=limit,
    )


@router.get("/{account_id}/", summary="Get Account by ID", response_model=api_models.Account)
def api_get_account(account: db_models.Account = Depends(get_account_from_path)):
    return account


@router.post(
    "/",
    summary="Create one or more Accounts",
    response_model=Union[api_models.Account, List[api_models.Account]],
)
def api_create_account(
    accounts: Union[api_models.AccountCreate, List[api_models.AccountCreate]],
    db_session: Session = Depends(get_db_session),
):
    if not isinstance(accounts, list):
        accounts = [accounts]

    new_accounts: List[db_models.Account] = [
        db_models.Account(**account.model_dump()) for account in accounts
    ]
    db_session.add_all(new_accounts)
    db_session.commit()
    for new_account in new_accounts:
        db_session.refresh(new_account)

    if len(new_accounts) == 1:
        new_accounts = new_accounts[0]
    return new_accounts


@router.get(
    "/{account_id}/transactions/",
    summary="List all transactions for the account",
    response_model=list[api_models.Transaction],
)
def api_get_transactions(
    account_id: int, skip: int = 0, limit: int = 100, db_session: Session = Depends(get_db_session)
):
    return crud.get_transactions(
        account_id=account_id,
        db_session=db_session,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{account_id}/transactions/",
    summary="Ingest transactions",
    response_model=api_models.IngestResult,
)
def api_ingest_transactions(
    upload_file: UploadFile,
    ingest_type: Optional[api_models.IngestType] = None,
    account: db_models.Account = Depends(get_account_from_path),
    db_session: Session = Depends(get_db_session),
):
    logger.info("ingesting")
    if ingest_type is None:
        ingest_type = account.default_ingest_type
    result = ingest_file(
        account_id=account.id,
        ingest_type=ingest_type,
        file=upload_file.file,
        db_session=db_session,
    )
    logger.info(f"Ingest result: {result}")
    return result


@router.get(
    "/{account_id}/balance/",
    summary="Get the account balance, optionaly for a specified time frame",
    response_model=Decimal,
)
def api_get_account_balance(
    account_id: int,
    start_date: Optional[datetime] = Depends(start_date_parser),
    end_date: Optional[datetime] = Depends(end_date_parser),
    db_session: Session = Depends(get_db_session),
):
    # todo customised by ac type (i.e. crowd property)
    # or could have an 'exclude from balance' field maybe and deal with it at ingest
    return crud.get_balance(
        db_session=db_session,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
    )

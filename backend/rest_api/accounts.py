import json
import logging
import zipfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path as PathLibPath
from tempfile import TemporaryDirectory, mkstemp
from typing import Dict, List, Optional, Union

from dateutil import parser
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from sqlalchemy.orm import Session

from backend import api_models, crud, db_models
from backend.db import get_db_session
from backend.ingest import ingest_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["Accounts"])


def parse_date(date_str: Optional[str] = None) -> Optional[datetime]:
    # logger.info(f"parsing date {date_str}")
    if date_str is None:
        return None
    try:
        # todo should we force a time zone? start_date = start_date.astimezone(pytz.utc)
        return parser.parse(
            date_str
        )  # , dayfirst=True) todo work out a date format to use across everything
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format {date_str}"
        )


def start_date_parser(start_date: Optional[str] = None) -> Optional[datetime]:
    # logger.info(f"parsing date {start_date}")
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
    db_session: Session = Depends(get_db_session),
):
    return crud.get_accounts(db_session=db_session, institution=institution, name=name)


@router.get(
    "/summary/",
    summary="Get a summary of all account data",
    response_model=List[api_models.AccountSummary],
)
def api_get_accounts_summary(
    interpolate: bool = True, db_session: Session = Depends(get_db_session)
):
    logger.info(f"Getting account summary, {interpolate=}")
    accounts: List[api_models.Account] = crud.get_accounts(db_session=db_session)
    monthly_balance_results: List[api_models.MonthlyBalanceResult] = crud.get_monthly_balances(
        db_session=db_session, interpolate=interpolate
    )
    last_transaction_dates: Dict[int, datetime] = crud.get_last_transaction_dates(
        db_session=db_session
    )

    results = []
    for account in accounts:
        # find the monthly balance result for this account
        monthly_balance_result = next(
            (
                monthly_balance_result
                for monthly_balance_result in monthly_balance_results
                if monthly_balance_result.account_id == account.id
            )
        )

        results.append(
            api_models.AccountSummary(
                account=account,
                monthly_balances=monthly_balance_result,
                last_transaction_date=last_transaction_dates.get(account.id, None),
            )
        )

    # sort accounts by earliest monthly balance
    # todo if we have broader types we can sort by type and then by date
    # would be good to sort by assets, pensions, savings, current, credit
    # for now just move the pension first after the basic sort
    results.sort(key=lambda x: x.monthly_balances.start_year_month)
    assets = [val for val in results if val.account.account_type == api_models.AccountType.asset]
    not_assets = [
        val for val in results if val.account.account_type != api_models.AccountType.asset
    ]
    return assets + not_assets


@router.get("/export/", summary="Get a backup of all accounts")
def api_export(background_tasks: BackgroundTasks, db_session: Session = Depends(get_db_session)):
    logger.info("Getting backup data")
    backup_data = crud.get_account_backup(db_session=db_session)
    logger.info("Saving backup data to zip")
    backup_datetime_str = backup_data.backup_datetime.strftime("%Y_%m_%d_%H_%M_%S")
    json_filename = f"backup_{backup_datetime_str}.json"
    zip_filename = f"backup_{backup_datetime_str}.zip"
    _, zip_file_path_str = mkstemp(suffix=".zip")
    zip_file_path = PathLibPath(zip_file_path_str)

    try:
        backup_json = json.dumps(backup_data.model_dump(), default=pydantic_encoder, indent=2)
        json_temp_path = zip_file_path.with_suffix(".json")

        with json_temp_path.open("w") as f:
            f.write(backup_json)

        with zipfile.ZipFile(zip_file_path, "w") as zip_file:
            zip_file.write(json_temp_path, arcname=json_filename)

        background_tasks.add_task(zip_file_path.unlink)
        background_tasks.add_task(json_temp_path.unlink)

        logger.info("Returning backup zip")
        return FileResponse(zip_file_path_str, filename=zip_filename, media_type="application/zip")
    except Exception as e:
        # In case of an error, remove any created files
        zip_file_path.unlink(missing_ok=True)
        json_temp_path.unlink(missing_ok=True)
        raise e


@router.post("/import/", summary="Import a previously exported backup zip file.")
async def import_backup(
    db_session: Session = Depends(get_db_session), file: UploadFile = File(...)
):
    # todo check db empty?
    if len(crud.get_accounts(db_session=db_session)) != 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database is not empty. Import cannot proceed.",
        )

    logger.info("Extracting backup data from zip")
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = PathLibPath(tmpdir)

        try:
            with zipfile.ZipFile(file.file) as zip_ref:
                zip_file_list = zip_ref.namelist()
                if len(zip_file_list) != 1 or not zip_file_list[0].endswith(".json"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ZIP file must contain exactly one .json file.",
                    )

                # Extract the JSON file
                zip_ref.extractall(tmpdir_path)
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid ZIP archive.",
            )

        json_file_path = tmpdir_path / zip_file_list[0]

        logger.info("Loading backup data from json")
        try:
            with open(json_file_path, "r") as json_file:
                backup_data = json.load(json_file)
                backup_model = api_models.BackupV1(**backup_data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise HTTPException(status_code=400, detail=f"Error processing JSON file: {str(e)}")

        logger.info(
            f"Loading {len(backup_model.accounts)} accounts from {backup_model.backup_datetime} to DB"
        )
        crud.restore_account_backup(db_session=db_session, backup=backup_model)
        logger.info("Restore complete")

        return status.HTTP_201_CREATED


### /{account_id}/ paths below here only ###


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
    return crud.create_accounts(db_session=db_session, accounts=accounts)


@router.get(
    "/{account_id}/transactions/",
    summary="List all transactions for the account",
    response_model=List[api_models.Transaction],
)
def api_get_transactions(
    account_id: int,
    start_date: Optional[datetime] = Depends(start_date_parser),
    end_date: Optional[datetime] = Depends(end_date_parser),
    db_session: Session = Depends(get_db_session),
):
    # logger.info(f"Getting transactions for account {account_id} from {start_date} to {end_date}")
    return crud.get_transactions(
        db_session=db_session, account_id=account_id, start_date=start_date, end_date=end_date
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
    if ingest_type is None:
        ingest_type = account.default_ingest_type
    result = ingest_file(
        account_id=account.id,
        ingest_type=ingest_type,
        file=upload_file.file,
        db_session=db_session,
    )
    logger.info(f"Ingest result: {result}")

    if result.transactions_inserted > 0:
        # todo run rules only on new transactions
        # todo can we make a trigger to make run rules happen? will this be a pain for tests?
        crud.run_rules(db_session=db_session, account_ids=account.id)
    return result


@router.get(
    "/{account_id}/balance/",
    summary="Get the account balance, optionaly for a specified time frame",
    response_model=api_models.BalanceResult,
)
def api_get_account_balance(
    account_id: int,  # todo could have a depends to check its a valid id or even make this the account object using a depends
    start_date: Optional[datetime] = Depends(start_date_parser),
    end_date: Optional[datetime] = Depends(end_date_parser),
    db_session: Session = Depends(get_db_session),
):
    return crud.get_balance(
        db_session=db_session,
        account_ids=[account_id],
        start_date=start_date,
        end_date=end_date,
    )[
        0
    ]  # todo placeholder until we ensure account_id is valid


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


def year_month(year_month: Optional[str] = None) -> Optional[datetime]:
    return parse_year_month(year_month)


@router.post(
    "/{account_id}/set-balance/",
    summary="Insert a transaction to adjust the end balance for a month. ",
    description="If there are later months a second transaction will be inserted to count the change for the next month.",
    response_model=Union[api_models.Transaction, List[api_models.Transaction]],
)
def api_set_balance(
    account: db_models.Account = Depends(get_account_from_path),
    year_month: Optional[datetime] = Depends(year_month),
    balance: Decimal = Query(...),
    deposits_to_date: Optional[Decimal] = Query(None),
    db_session: Session = Depends(get_db_session),
):
    return crud.set_balance(
        db_session=db_session,
        account_id=account.id,
        balance=balance,
        deposits_to_date=deposits_to_date,
        year_month=year_month,
    )

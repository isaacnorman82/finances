import csv
import io
import logging
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from tempfile import SpooledTemporaryFile
from typing import Any, Dict, Iterable, List, Optional, Set

from fastapi import HTTPException, status
from ofxtools.Parser import OFXTree
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import api_models, db_models
from backend.api_models import IngestType

logger = logging.getLogger(__name__)


class FileIngester(ABC):
    account_id: int
    db_session: Session
    transactions: List[db_models.Transaction]

    def __init__(self, account_id: int, db_session: Session):
        self.account_id = account_id
        self.db_session = db_session
        self.transactions = []

    @abstractmethod
    def ingest(self, file: SpooledTemporaryFile) -> api_models.IngestResult:
        pass

    def create_transaction(
        self, date_str: str, date_fmt: str, amount: Decimal, **kwargs: Dict[str, str]
    ) -> db_models.Transaction:
        kwargs["account_id"] = self.account_id
        kwargs["date_time"] = datetime.strptime(date_str, date_fmt)
        kwargs["amount"] = amount
        return db_models.Transaction(**kwargs)

    # todo maybe different strategies for replacement
    # nationwide could always insert after existing entires up until end_date-1, should avoid incomplete days
    # crowd property prob won't have tagging so could just replace or could use the more exact times to just add new ones
    def store_transactions(self) -> api_models.IngestResult:
        result: api_models.IngestResult = api_models.IngestResult(account_id=self.account_id)

        if not self.transactions:
            return result

        result.start_date = min(self.transactions, key=lambda tx: tx.date_time).date_time
        result.end_date = max(self.transactions, key=lambda tx: tx.date_time).date_time
        result.transactions_deleted = self.delete_transactions(result.start_date, result.end_date)
        result.transactions_inserted = len(self.transactions)
        self.db_session.bulk_save_objects(self.transactions)
        self.db_session.commit()
        return result

    def delete_transactions(self, start_date: datetime, end_date: datetime) -> int:
        stmt = delete(db_models.Transaction).where(
            db_models.Transaction.date_time.between(start_date, end_date)
            & (db_models.Transaction.account_id == self.account_id)
        )
        result = self.db_session.execute(stmt)
        return result.rowcount


class OFXFileIngester(FileIngester):
    def ingest(self, file: SpooledTemporaryFile) -> api_models.IngestResult:
        parser = OFXTree()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # # Read the contents of the SpooledTemporaryFile into memory
            # file_contents = file.read()

            # # Create an in-memory file-like object from the file contents
            # file_stream = io.BytesIO(file_contents)

            # logger.info("Parsing OFX file")
            # parser.parse(file_stream)

            parser.parse(file)

            # work around for this issue https://github.com/csingley/ofxtools/issues/188
            # could fork ofxtools and make the fix myself but this avoids a fork for now
            # hsbc ofx file has empty memo's which trips up the ofxtools convert function
            # work around by setting it to something that evalutes to true, we don't use it anyway
            memos = parser._root.findall(".//MEMO")
            for memo in memos:
                if memo.text is None:
                    memo.text = " "

            ofx = parser.convert()

        logger.info(f"Found {len(ofx.statements[0].transactions)} transactions in OFX file")

        self.transactions = [
            db_models.Transaction(
                account_id=self.account_id,
                date_time=tx.dtposted,
                amount=tx.trnamt,
                transaction_type=tx.trntype,
                description=tx.name,
                # fitid=tx.fitid,
            )
            for tx in ofx.statements[0].transactions
        ]
        return self.store_transactions()


class CSVFileIngester(FileIngester):
    REQUIRED_FIELDS = {"date", "description", "amount"}
    ENCODING: str = "UTF-8"

    def create_transaction_from_record(self, record: Dict[str, str]) -> None:
        self.transactions.append(
            super().create_transaction(
                date_str=record["date"],
                date_fmt="%d/%m/%Y",
                amount=Decimal(record["amount"]),
                description=record["description"],
                transaction_type=record.get("transaction_type", None),
                notes=record.get("notes", None),
                reference=record.get("reference", None),
            )
        )

    def ingest(self, file: SpooledTemporaryFile) -> api_models.IngestResult:
        text = io.TextIOWrapper(file, encoding=self.ENCODING)
        reader = csv.DictReader(text)

        if not self.REQUIRED_FIELDS.issubset(set(reader.fieldnames)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Did not find expected headings {self.REQUIRED_FIELDS}.  Found {reader.fieldnames}",
            )

        for record in reader:
            try:
                self.create_transaction_from_record(record=record)
            except Exception as ex:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse record: {record}.  Details: {ex}",
                )

        return self.store_transactions()


class CrowdPropertyIngester(CSVFileIngester):
    REQUIRED_FIELDS = {"Date", "Transaction", "Type", "To", "Reference"}

    def create_transaction_from_record(self, record: Dict[str, str]) -> None:
        if record["Type"] in ["Not Set", "Interest Payment - Reinvest"]:
            # we only want an accurate balance from this data so only
            # use deposits and interest.  This might miss issues such as
            # investments that only pay back partial amounts.
            self.transactions.append(
                super().create_transaction(
                    date_str=record["Date"],
                    date_fmt="%d-%b-%Y %H:%M:%S",
                    amount=Decimal(record["Transaction"]),
                    transaction_type=record["Type"],
                    description=record["To"],
                    reference=record["Reference"],
                )
            )


class MoneyFarmIngester(CSVFileIngester):
    REQUIRED_FIELDS = {"Date", "Market value", "Net contributions"}
    date_fmt = "%Y-%m-%d"

    prev_net_contrib: Decimal = Decimal("0")
    prev_market_value: Decimal = Decimal("0")

    def create_transaction_from_record(self, record: Dict[str, str]) -> None:
        new_net_contrib = Decimal(record["Net contributions"])
        new_market_value = Decimal(record["Market value"])
        contrib_amount = new_net_contrib - self.prev_net_contrib

        if new_net_contrib > self.prev_net_contrib:

            self.transactions.append(
                super().create_transaction(
                    date_str=record["Date"],
                    date_fmt=self.date_fmt,
                    amount=contrib_amount,
                    transaction_type="deposit",
                    description="Deposit" if contrib_amount > 0 else "Withdrawal",
                )
            )

        if new_market_value != self.prev_market_value + contrib_amount:
            self.transactions.append(
                super().create_transaction(
                    date_str=record["Date"],
                    date_fmt=self.date_fmt,
                    amount=new_market_value - (self.prev_market_value + contrib_amount),
                    transaction_type="value adjustment",
                    description="Market value change",
                )
            )

        self.prev_net_contrib = new_net_contrib
        self.prev_market_value = new_market_value


def ingest_file(
    account_id: int, ingest_type: IngestType, file: SpooledTemporaryFile, db_session: Session
) -> api_models.IngestResult:
    # todo a map might be cleaner here
    match ingest_type:
        case IngestType.csv:
            ingest_class = CSVFileIngester
        case IngestType.ofx_transactions:
            ingest_class = OFXFileIngester
        case IngestType.crowd_property_csv:
            ingest_class = CrowdPropertyIngester
        case IngestType.money_farm_csv:
            ingest_class = MoneyFarmIngester
        case _:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ingest type {ingest_type} not supported!",
            )

    return ingest_class(account_id=account_id, db_session=db_session).ingest(file=file)

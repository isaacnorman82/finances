from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum, auto
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator

_orm_config = ConfigDict(from_attributes=True, extra="forbid")


class AcType(StrEnum):
    current_account = auto()
    asset = auto()
    cash_isa = auto()
    credit_card = auto()
    if_isa = auto()
    junior_isa = auto()
    loan = auto()
    mortgage = auto()
    pension = auto()
    savings_account = auto()
    share_isa = auto()
    stockbroker = auto()


class AcBehaviour(StrEnum):
    standard = auto()
    crowd_property = auto()


class IngestType(StrEnum):
    crowd_property_csv = auto()
    csv = auto()
    money_farm_csv = auto()
    ofx_transactions = auto()


class AccountCreate(BaseModel):
    institution: str
    name: str
    account_type: AcType
    account_behaviour: AcBehaviour = AcBehaviour.standard
    default_ingest_type: IngestType = IngestType.csv
    is_active: bool = True
    # transactions: List[Transaction]  - could add this in but need to understand what triggers population (i.e. avoid always fetching all)
    description: Optional[str] = None


class Account(AccountCreate):
    model_config = _orm_config
    id: int


class TransactionCreate(BaseModel):
    account_id: int
    date_time: datetime
    amount: Decimal
    transaction_type: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount", mode="before")
    def validate_and_round_amount(cls, value):
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Transaction(TransactionCreate):
    model_config = _orm_config
    id: int
    # account: Account - would adding this in be inefficient with lots of transactions?


class IngestResult(BaseModel):
    account_id: int
    transactions_deleted: int = 0
    transactions_inserted: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BalanceResult(BaseModel):
    account_id: int
    balance: Decimal
    last_transaction_date: Optional[datetime] = None  # optional in case no transactions were found
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class MonthlyBalance(BaseModel):
    year_month: str
    start_balance: Decimal
    monthly_balance: Decimal
    end_balance: Decimal


class MonthlyBalanceResult(BaseModel):
    account_id: int
    monthly_balances: List[MonthlyBalance]
    start_year_month: str
    end_year_month: str


class AccountSummary(BaseModel):
    account: Account
    balance: Decimal
    monthly_balances: MonthlyBalanceResult
    last_transaction_date: Optional[datetime] = None

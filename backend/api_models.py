from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum, auto
from typing import List, Literal, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator

logger = logging.getLogger(__name__)

_orm_config = ConfigDict(from_attributes=True, extra="forbid")


# todo simplify? maybe just monthly ones (current/cc) savings and pensions? or have another mapping for that?
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


class IngestType(StrEnum):
    crowd_property_csv = auto()
    csv = auto()
    value_and_contrib_csv = auto()
    ofx_transactions = auto()


# class RuleConditionID(StrEnum):
#     base = "base"
#     contains_any = "contains_any"


class AccountCreate(BaseModel):
    institution: str
    name: str
    account_type: AcType
    default_ingest_type: IngestType = IngestType.csv
    is_active: bool = True
    description: Optional[str] = None
    ac_number: Optional[str] = None
    external_link: Optional[str] = None


class Account(AccountCreate):
    model_config = _orm_config
    id: int


class RuleCondition(BaseModel, ABC):
    type_id: Literal["invalid"]

    class Config:
        use_enum_values = True
        discriminator = "type_id"

    @abstractmethod
    def evaluate(self, transaction: Transaction) -> bool:
        pass


class IsValueAdjContainsAny(RuleCondition):
    type_id: Literal["is_value_adj_contains_any"]
    values: List[str]
    read_col: str = "description"

    @field_validator("values", mode="before")
    def values_to_lower(cls, value):
        return [val.lower() for val in value]

    def evaluate(self, transaction: Transaction):
        input = getattr(transaction, self.read_col).lower()
        transaction.is_value_adjustment = any(val in input for val in self.values)
        # logger.info(f"{input=}, {transaction.is_value_adjustment=} {self.values=}")


class TransactionRuleCreate(BaseModel):
    account_id: int
    condition: Union[RuleCondition, IsValueAdjContainsAny]


class TransactionRule(TransactionRuleCreate):
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
    is_value_adjustment: Optional[bool] = False

    @field_validator("amount", mode="before")
    def validate_and_round_amount(cls, value):
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Transaction(TransactionCreate):
    model_config = _orm_config
    id: int


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
    deposits_to_date: Decimal


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


class DataSeriesCreate(BaseModel):
    date_time: datetime
    key: str
    value: str


class DataSeries(DataSeriesCreate):
    model_config = _orm_config
    id: int


class AddDataSeriesResult(BaseModel):
    values_added: int

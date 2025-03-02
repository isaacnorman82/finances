from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum, auto
from typing import List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    FieldValidationInfo,
    computed_field,
    field_validator,
)

logger = logging.getLogger(__name__)

_orm_config = ConfigDict(from_attributes=True, extra="forbid")


def validate_decimal_places(
    value: Decimal, field_name: str, model_name: str, decimal_places: int = 2
) -> Decimal:
    # Validator function to check if a Decimal value has more than `decimal_places` places.
    quantized_value = value.quantize(Decimal("1." + "0" * decimal_places), rounding=ROUND_HALF_UP)
    if value != quantized_value:
        raise ValueError(
            f'{model_name}: The field "{field_name}" has more than {decimal_places} decimal places. '
            f"Given value: {value}"
        )
    return value


class AccountType(StrEnum):
    current_credit = "Current/Credit"
    asset = "Asset"
    savings = "Savings"
    loans = "Loan"
    pensions = "Pension"


class IngestType(StrEnum):
    crowd_property_csv = auto()
    csv = auto()
    value_and_contrib_csv = auto()
    ofx_transactions = auto()
    amex_csv = auto()


class InterpolationType(StrEnum):
    none = auto()
    inter = auto()
    end = auto()


class AccountCreate(BaseModel):
    model_config = _orm_config
    institution: str
    name: str
    account_type: AccountType
    default_ingest_type: IngestType = IngestType.csv
    is_active: bool = True
    description: Optional[str] = None
    ac_number: Optional[str] = None
    external_link: Optional[str] = None


class Account(AccountCreate):
    id: int


class RuleCondition(BaseModel, ABC):
    type_id: Literal["invalid"] = "invalid"

    class Config:
        use_enum_values = True
        discriminator = "type_id"

    @abstractmethod
    def evaluate(self, transaction: Transaction) -> bool:
        pass


class IsValueAdjContainsAny(RuleCondition):
    type_id: Literal["is_value_adj_contains_any"] = "is_value_adj_contains_any"
    values: List[str]
    read_col: str = "description"

    @field_validator("values", mode="before")
    def values_to_lower(cls, value):
        return [val.lower() for val in value]

    def evaluate(self, transaction: Transaction):
        # todo currently we overwrite is_value_adjustment even if it was specifically set true
        # when the transaction was created
        input = getattr(transaction, self.read_col).lower()
        transaction.is_value_adjustment = any(val in input for val in self.values)
        # logger.info(f"{input=}, {transaction.is_value_adjustment=} {self.values=}")


class TransactionRuleCreate(BaseModel):
    model_config = _orm_config
    account_id: int
    condition: Union[RuleCondition, IsValueAdjContainsAny]


class TransactionRule(TransactionRuleCreate):
    id: int


class TransactionCreate(BaseModel):
    model_config = _orm_config
    account_id: int
    date_time: datetime
    amount: Decimal
    transaction_type: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    is_value_adjustment: Optional[bool] = False

    # @field_validator("amount", mode="before")
    # def validate_and_round_amount(cls, value):
    #     return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("amount", mode="after")
    def validate_dp(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "amount", cls.__name__)


class Transaction(TransactionCreate):
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
    deposits_to_date: Decimal
    last_transaction_date: Optional[datetime] = None  # optional in case no transactions were found
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("balance", mode="after")
    def validate_dp(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "balance", cls.__name__)

    @field_validator("deposits_to_date", mode="after")
    def validate_dp_dtd(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "deposits_to_date", cls.__name__)


class MonthlyBalance(BaseModel):
    year_month: str
    start_balance: Decimal
    monthly_balance: Decimal  # todo make property and rename to balance
    end_balance: Decimal
    deposits_to_date: Decimal
    interpolated: InterpolationType = InterpolationType.none

    @field_validator("start_balance", mode="after")
    def validate_dp_sb(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "start_balance", cls.__name__)

    @field_validator("monthly_balance", mode="after")
    def validate_dp_mb(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "monthly_balance", cls.__name__)

    @field_validator("end_balance", mode="after")
    def validate_dp_eb(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "end_balance", cls.__name__)

    @field_validator("deposits_to_date", mode="after")
    def validate_dp_dtd(cls, value: Decimal) -> Decimal:
        return validate_decimal_places(value, "deposits_to_date", cls.__name__)


class MonthlyBalanceResult(BaseModel):
    account_id: int  # todo be nice to remove this
    monthly_balances: List[MonthlyBalance]
    # start_year_month: str  # todo what if there are no transactions?
    # end_year_month: str

    @computed_field
    @property
    def start_year_month(self) -> str:
        # todo test with accounts with no transactions
        return self.monthly_balances[0].year_month

    @computed_field
    @property
    def end_year_month(self) -> str:
        return self.monthly_balances[-1].year_month


class AccountSummary(BaseModel):
    account: Account
    # balance: Decimal
    monthly_balances: MonthlyBalanceResult
    last_transaction_date: Optional[datetime] = None

    @computed_field
    @property
    def balance(self) -> Decimal:
        return self.monthly_balances.monthly_balances[-1].end_balance


class DataSeriesCreate(BaseModel):
    model_config = _orm_config
    date_time: datetime
    key: str
    value: str


class DataSeries(DataSeriesCreate):
    id: int


class AddDataSeriesResult(BaseModel):
    values_added: int


class AccountBackup(BaseModel):
    account: AccountCreate
    rule_conditions: List[Union[RuleCondition, IsValueAdjContainsAny]] = []
    transactions: List[TransactionCreate] = []


class Backup(BaseModel, ABC):
    version: Literal["invalid"] = "invalid"

    class Config:
        use_enum_values = True
        discriminator = "version"

    # @abstractmethod
    # def upgrade(self, transaction: Transaction) -> bool:
    #     pass
    # in future a BackupV2 can implement upgrade(backupV1)


class BackupV1(Backup):
    version: Literal["1.0.0"] = "1.0.0"
    backup_datetime: str = str(datetime.now(timezone.utc))
    accounts: List[AccountBackup] = []
    data_series: List[DataSeriesCreate] = []

    @property
    def backup_datetime(self) -> str:
        return str(datetime.now(timezone.utc))

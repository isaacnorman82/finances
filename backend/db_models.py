from functools import partial

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.api_models import AcType, IngestType
from backend.db import Base

ReqCol = partial(Column, nullable=False)
OptCol = partial(Column, nullable=True)


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)

    # required fields
    name = ReqCol(String, index=True)
    account_type = ReqCol(Enum(AcType), index=True)
    institution = ReqCol(String, index=True)
    is_active = ReqCol(Boolean, default=True)
    default_ingest_type: IngestType = ReqCol(Enum(IngestType))

    # optional fields
    description = OptCol(String)
    ac_number = OptCol(String)
    external_link = OptCol(String)

    # relationships
    transactions = relationship("Transaction", back_populates="account")
    transaction_rules = relationship("TransactionRule", back_populates="account")

    # Define a composite unique constraint
    __table_args__ = (UniqueConstraint("institution", "name", name="unique_institution_name"),)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)

    # required fields
    account_id = ReqCol(Integer, ForeignKey("accounts.id"))
    date_time = ReqCol(DateTime, index=True)
    amount = ReqCol(DECIMAL(precision=10, scale=2))
    is_value_adjustment = ReqCol(Boolean, default=False)

    # optional fields
    transaction_type = OptCol(String, index=True)
    description = OptCol(String, index=True)
    # fitid = OptCol(String, index=True, unique=True)
    reference = OptCol(String, index=True)
    notes = OptCol(String, index=True)

    # relationships
    account = relationship("Account", back_populates="transactions")


class TransactionRule(Base):
    __tablename__ = "transaction_rule"
    id = Column(Integer, primary_key=True)

    # required fields
    account_id = ReqCol(Integer, ForeignKey("accounts.id"))
    condition = ReqCol(JSONB)

    # relationships
    account = relationship("Account", back_populates="transaction_rules")


# todo will need tags on transactions
# might be helpful: https://www.databasesoup.com/2015/01/tag-all-things.html


class DataSeries(Base):
    __tablename__ = "data_series"
    id = Column(Integer, primary_key=True)

    # required fields
    date_time = ReqCol(DateTime, index=True)
    key = ReqCol(String, index=True)
    value = ReqCol(String)

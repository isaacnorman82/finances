from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import db_models


def get_account(account_id: int, db_session: Session) -> Optional[db_models.Account]:
    return db_session.query(db_models.Account).get(account_id)


def get_accounts(
    db_session: Session,
    institution: Optional[str] = None,
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[db_models.Account]:
    query = db_session.query(db_models.Account)

    if institution:
        query = query.filter(db_models.Account.institution == institution)
    if name:
        query = query.filter(db_models.Account.name == name)

    return query.offset(skip).limit(limit).all()


def get_transactions(
    account_id: int, db_session: Session, skip: int = 0, limit: int = 100
) -> List[db_models.Transaction]:
    return (
        db_session.query(db_models.Transaction)
        .filter(db_models.Transaction.account_id == account_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_balance(
    db_session: Session,
    account_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Decimal:
    query = db_session.query(func.sum(db_models.Transaction.amount))

    if account_id:
        query = query.filter(db_models.Transaction.account_id == account_id)
    if start_date:
        query = query.filter(db_models.Transaction.date_time >= start_date)
    if end_date:
        query = query.filter(db_models.Transaction.date_time <= end_date)

    return query.scalar()

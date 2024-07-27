import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import api_models, db_models

logger = logging.getLogger(__name__)


def get_account(account_id: int, db_session: Session) -> Optional[db_models.Account]:
    return db_session.query(db_models.Account).get(account_id)


def get_accounts(
    db_session: Session,
    institution: Optional[str] = None,
    name: Optional[str] = None,
    skip: int = 0,  # todo make optional
    limit: int = 100,
) -> List[api_models.Account]:
    query = db_session.query(db_models.Account)

    if institution:
        query = query.filter(db_models.Account.institution == institution)
    if name:
        query = query.filter(db_models.Account.name == name)

    results = query.offset(skip).limit(limit).all()
    return [api_models.Account.model_validate(result) for result in results]


def get_transactions(
    db_session: Session,
    account_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = None,
    limit: int = None,
) -> List[db_models.Transaction]:

    query = db_session.query(db_models.Transaction).filter(
        db_models.Transaction.account_id == account_id
    )

    if start_date:
        query = query.filter(db_models.Transaction.date_time >= start_date)

    if end_date:
        query = query.filter(db_models.Transaction.date_time <= end_date)

    if skip is not None:
        query = query.offset(skip)

    if limit is not None:
        query = query.limit(limit)

    query.order_by(db_models.Transaction.date_time.asc())

    results = query.all()

    return [api_models.Transaction.model_validate(result) for result in results]


def get_balance(
    db_session: Session,
    account_ids: Optional[List[int]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[api_models.BalanceResult]:
    results = []

    # Create base queries
    balance_query = db_session.query(
        db_models.Transaction.account_id, func.sum(db_models.Transaction.amount).label("balance")
    )
    max_date_query = db_session.query(
        db_models.Transaction.account_id,
        func.max(db_models.Transaction.date_time).label("last_transaction_date"),
    )

    # Apply filters
    if account_ids:
        balance_query = balance_query.filter(db_models.Transaction.account_id.in_(account_ids))
        max_date_query = max_date_query.filter(db_models.Transaction.account_id.in_(account_ids))
    if start_date:
        balance_query = balance_query.filter(db_models.Transaction.date_time >= start_date)
        max_date_query = max_date_query.filter(db_models.Transaction.date_time >= start_date)
    if end_date:
        balance_query = balance_query.filter(db_models.Transaction.date_time <= end_date)
        max_date_query = max_date_query.filter(db_models.Transaction.date_time <= end_date)

    # Group by account ID
    balance_query = balance_query.group_by(db_models.Transaction.account_id)
    max_date_query = max_date_query.group_by(db_models.Transaction.account_id)

    # Execute the queries and create results
    balance_results = {row.account_id: row.balance for row in balance_query.all()}
    max_date_results = {row.account_id: row.last_transaction_date for row in max_date_query.all()}

    all_account_ids = account_ids or list(balance_results.keys())

    for account_id in all_account_ids:
        balance = balance_results.get(account_id, Decimal(0))
        last_transaction_date = max_date_results.get(account_id)
        results.append(
            api_models.BalanceResult(
                account_id=account_id,
                balance=balance,
                last_transaction_date=last_transaction_date,
                start_date=start_date,
                end_date=end_date,
            )
        )

    return results


def get_first_day_of_next_month(date: datetime) -> datetime:
    next_month = date.replace(day=28) + timedelta(days=4)  # this will never fail
    return next_month.replace(day=1)


def get_monthly_balances(
    db_session: Session,
    account_ids: Optional[List[int]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[api_models.MonthlyBalanceResult]:

    if end_date:
        end_date = get_first_day_of_next_month(end_date)
        logger.info(f"end_date: {end_date}")

    # Build the base query
    base_query = db_session.query(
        db_models.Transaction.account_id,
        func.date_trunc("month", db_models.Transaction.date_time).label("month"),
        func.sum(db_models.Transaction.amount).label("monthly_balance"),
    ).group_by(
        db_models.Transaction.account_id, func.date_trunc("month", db_models.Transaction.date_time)
    )

    # Apply filters if provided
    if account_ids is not None:
        base_query = base_query.filter(db_models.Transaction.account_id.in_(account_ids))

    if start_date is not None:
        base_query = base_query.filter(db_models.Transaction.date_time >= start_date)

    if end_date is not None:
        base_query = base_query.filter(db_models.Transaction.date_time < end_date)

    # Subquery for cumulative balance
    subquery = base_query.subquery()

    cumulative_balance_query = (
        db_session.query(
            subquery.c.account_id,
            subquery.c.month,
            subquery.c.monthly_balance,
            func.sum(subquery.c.monthly_balance)
            .over(partition_by=subquery.c.account_id, order_by=subquery.c.month)
            .label("cumulative_balance"),
        )
        .order_by(subquery.c.account_id, subquery.c.month)
        .all()
    )

    # Process results
    results = {}
    for row in cumulative_balance_query:
        account_id = row.account_id
        year_month_str = row.month.strftime("%Y-%m")

        if account_id not in results:
            results[account_id] = api_models.MonthlyBalanceResult(
                account_id=account_id,
                monthly_balances=[],
                start_year_month=year_month_str,
                end_year_month=year_month_str,
            )
        else:
            results[account_id].end_year_month = year_month_str

        monthly_balance = api_models.MonthlyBalance(
            year_month=year_month_str,
            monthly_balance=Decimal(row.monthly_balance),
            cumulative_balance=Decimal(row.cumulative_balance),
        )

        results[account_id].monthly_balances.append(monthly_balance)

    return list(results.values())

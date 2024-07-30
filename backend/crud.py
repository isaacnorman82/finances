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
    db_session: Session, account_ids: Optional[List[int]] = None
) -> List[api_models.MonthlyBalanceResult]:

    # Build the base query for monthly balances and cumulative balance
    base_query = db_session.query(
        db_models.Transaction.account_id,
        func.date_trunc("month", db_models.Transaction.date_time).label("month"),
        func.sum(db_models.Transaction.amount).label("monthly_balance"),
        func.sum(func.sum(db_models.Transaction.amount))
        .over(
            partition_by=db_models.Transaction.account_id,
            order_by=func.date_trunc("month", db_models.Transaction.date_time),
        )
        .label("cumulative_balance"),
    ).group_by(
        db_models.Transaction.account_id, func.date_trunc("month", db_models.Transaction.date_time)
    )

    # Apply filters for the query
    if account_ids is not None:
        base_query = base_query.filter(db_models.Transaction.account_id.in_(account_ids))

    # Execute the query
    monthly_balance_query = base_query.all()

    # Process results
    results = {}
    for row in monthly_balance_query:
        account_id = row.account_id
        year_month_str = row.month.strftime("%Y-%m")

        if account_id not in results:
            start_balance = Decimal(0)
            results[account_id] = api_models.MonthlyBalanceResult(
                account_id=account_id,
                monthly_balances=[],
                start_year_month=year_month_str,
                end_year_month=year_month_str,
            )
        else:
            results[account_id].end_year_month = year_month_str
            previous_month_balance = results[account_id].monthly_balances[-1].end_balance
            start_balance = previous_month_balance

        monthly_balance = Decimal(row.monthly_balance)
        end_balance = start_balance + monthly_balance

        monthly_balance_obj = api_models.MonthlyBalance(
            year_month=year_month_str,
            start_balance=start_balance,
            monthly_balance=monthly_balance,
            end_balance=end_balance,
        )

        results[account_id].monthly_balances.append(monthly_balance_obj)

    # Fill in the missing months with zero balances for each account
    for account_id, result in results.items():
        fill_missing_months(result.monthly_balances)

    return list(results.values())


def fill_missing_months(
    monthly_balances: List[api_models.MonthlyBalance],
) -> List[api_models.MonthlyBalance]:
    if not monthly_balances:
        return monthly_balances

    year, month = map(int, monthly_balances[0].year_month.split("-"))

    for i in range(1, len(monthly_balances) - 1):
        month = (month % 12) + 1
        if month == 1:
            year += 1

        if monthly_balances[i].year_month != f"{year:04d}-{month:02d}":
            monthly_balances.insert(
                i,
                api_models.MonthlyBalance(
                    year_month=f"{year:04d}-{month:02d}",
                    start_balance=monthly_balances[i - 1].end_balance,
                    monthly_balance=Decimal(0),
                    end_balance=monthly_balances[i - 1].end_balance,
                ),
            )

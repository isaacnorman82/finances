import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, text
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
    as_db_model: bool = False,
) -> List[db_models.Transaction] | List[api_models.Transaction]:

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

    query = query.order_by(db_models.Transaction.date_time.asc())

    logger.info(str(query.statement.compile(compile_kwargs={"literal_binds": True})))

    results = query.all()

    if as_db_model:
        return results
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

    # Prepare the SQL text query
    sql_query = """
        SELECT
            account_id,
            DATE_TRUNC('month', date_time) AS month,
            SUM(amount) AS monthly_balance,
            SUM(SUM(amount)) OVER (
                PARTITION BY account_id
                ORDER BY DATE_TRUNC('month', date_time)
            ) AS cumulative_balance,
            SUM(CASE WHEN is_value_adjustment THEN 0 ELSE amount END) AS monthly_deposit,
            SUM(SUM(CASE WHEN is_value_adjustment THEN 0 ELSE amount END)) OVER (
                PARTITION BY account_id
                ORDER BY DATE_TRUNC('month', date_time)
            ) AS cumulative_deposits
        FROM transactions
        {where_clause}
        GROUP BY account_id, DATE_TRUNC('month', date_time)
        ORDER BY account_id, month;
    """

    # Prepare the WHERE clause if account_ids are provided
    where_clause = ""
    if account_ids:
        where_clause = "WHERE account_id IN :account_ids"

    sql_query = sql_query.format(where_clause=where_clause)

    # Execute the SQL query
    result = db_session.execute(
        text(sql_query), {"account_ids": tuple(account_ids)} if account_ids else {}
    ).fetchall()

    # Process results
    results = {}

    for row in result:
        account_id = row[0]
        year_month_str = row[1].strftime("%Y-%m")

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

        monthly_balance = Decimal(row[2])
        end_balance = start_balance + monthly_balance
        deposits_to_date = Decimal(row[5])  # Cumulative deposits

        monthly_balance_obj = api_models.MonthlyBalance(
            year_month=year_month_str,
            start_balance=start_balance,
            monthly_balance=monthly_balance,
            end_balance=end_balance,
            deposits_to_date=deposits_to_date,
        )

        results[account_id].monthly_balances.append(monthly_balance_obj)

    # Fill in the missing months where there were no transactions
    for account_id, result in results.items():
        result.monthly_balances = fill_missing_months(result.monthly_balances)

    return list(results.values())


def fill_missing_months(
    monthly_balances: List[api_models.MonthlyBalance],
) -> List[api_models.MonthlyBalance]:
    if not monthly_balances:
        return monthly_balances

    def next_year_month(year_month: str) -> str:
        year, month = map(int, year_month.split("-"))
        month = (month % 12) + 1
        if month == 1:
            year += 1
        return f"{year:04d}-{month:02d}"

    results = [monthly_balances.pop(0)]

    while monthly_balances:
        while monthly_balances and monthly_balances[0].year_month != next_year_month(
            results[-1].year_month
        ):
            results.append(
                api_models.MonthlyBalance(
                    year_month=next_year_month(results[-1].year_month),
                    start_balance=results[-1].end_balance,
                    monthly_balance=Decimal(0),
                    end_balance=results[-1].end_balance,
                    deposits_to_date=results[-1].deposits_to_date,
                )
            )
        if monthly_balances:
            results.append(monthly_balances.pop(0))

    return results


# todo split this file up


def get_transaction_rule(id: int, db_session: Session) -> api_models.TransactionRule:
    result = db_session.query(db_models.TransactionRule).get(id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction Rule {id=} not found"
        )

    return api_models.TransactionRule.model_validate(result)


def get_rules(
    db_session: Session,
    account_ids: Optional[List[int]] = None,
    as_api_models: bool = True,
) -> List[api_models.TransactionRule]:
    query = db_session.query(db_models.TransactionRule)

    if account_ids is not None:
        query = query.filter(db_models.TransactionRule.account_id.in_(account_ids))

    results = query.all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No rules found for {account_ids=}"
        )

    if not as_api_models:
        return results
    return [api_models.TransactionRule.model_validate(result) for result in results]


def run_rules(db_session: Session, account_ids: Optional[List[int]] = None):
    rules: List[api_models.TransactionRule] = get_rules(
        db_session=db_session,
        account_ids=account_ids,
        as_api_models=True,
    )

    try:
        for rule in rules:
            transactions: List[api_models.Transaction] = get_transactions(
                db_session=db_session, account_id=rule.account_id
            )

            logger.info(
                f"Running rule {id=}, condition type {rule.condition.__class__.__name__}"
                f" on account_id={rule.account_id} for {len(transactions)} transactions"
            )

            for transaction in transactions:
                rule.condition.evaluate(transaction)
                db_session.merge(db_models.Transaction(**transaction.model_dump()))

        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise
    finally:
        db_session.close()

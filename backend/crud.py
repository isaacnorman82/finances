import logging
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Union

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

    # get the account objects
    accounts = get_accounts(db_session)

    # Fill in the missing months where there were no transactions
    for account_id, result in results.items():
        # add a final value to the current date for accounts we don't have up to date data for
        account = next(account for account in accounts if account.id == account_id)
        interpolate_to_current_date(account, result)

        # gap fill to ensure we have data for all months up to the current month
        fill_missing_months(account, result)

    # sort by earliest start date
    results = dict(sorted(results.items(), key=lambda item: item[1].start_year_month))

    return list(results.values())


def interpolate_to_current_date(
    account: api_models.Account,
    monthly_balance_result: api_models.MonthlyBalanceResult,
):
    if not account.is_active:
        # don't extend closed accounts
        return

    # todo find places that do this test and maybe have a specific account flag
    if account.default_ingest_type != api_models.IngestType.value_and_contrib_csv:
        # don't want to interpolate end values for these accounts
        return

    now_year_month: str = datetime.now().strftime("%Y-%m")

    if monthly_balance_result.end_year_month == now_year_month:
        # nothing to do
        return

    # decide how much the balance and deposits would grow in the time
    if len(monthly_balance_result.monthly_balances) == 0:
        # can't interpolate from nothing
        return
    elif len(monthly_balance_result.monthly_balances) == 1:
        end_balance = get_interpolated_monthly_balance(
            monthly_balance_result.monthly_balances[-1],
            now_year_month,
            api_models.InterpolationType.end,
        )
    else:
        end_balance = get_interpolated_balance_predict_growth(
            monthly_balance_result.monthly_balances, now_year_month, account.account_type
        )

    monthly_balance_result.end_year_month = now_year_month
    monthly_balance_result.monthly_balances.append(end_balance)


def fill_missing_months(
    account: api_models.Account,
    monthly_balance_result: api_models.MonthlyBalanceResult,
) -> List[api_models.MonthlyBalance]:
    if not monthly_balance_result.monthly_balances:
        return

    def next_year_month(year_month: str) -> str:
        year, month = map(int, year_month.split("-"))
        month = (month % 12) + 1
        if month == 1:
            year += 1
        return f"{year:04d}-{month:02d}"

    monthly_balances = monthly_balance_result.monthly_balances

    results = [monthly_balances.pop(0)]

    while monthly_balances:
        gap_size = get_num_months_between(
            results[-1].year_month,
            monthly_balances[0].year_month,
        )
        # if monthly_balances[0].year_month != next_year_month(results[-1].year_month):

        if gap_size > 1:
            monthly_balance = Decimal(0)
            monthly_deposit = Decimal(0)

            if account.default_ingest_type == api_models.IngestType.value_and_contrib_csv:
                cur_balance = results[-1].end_balance
                target_deposits = (
                    monthly_balances[0].deposits_to_date - results[-1].deposits_to_date
                )
                monthly_deposit = Decimal(target_deposits / gap_size)
                req_value_change = monthly_balances[0].end_balance - target_deposits - cur_balance
                monthly_balance = Decimal(req_value_change / gap_size)
                logger.info(
                    f"{cur_balance=}, {target_deposits=}, {monthly_deposit=}, {req_value_change=}"
                )

            logger.info(
                f"Account {account.id} Gap filling {gap_size=} for {results[-1].year_month}, {monthly_balance=}, {monthly_deposit=}"
            )
            for _ in range(gap_size - 1):
                results.append(
                    get_interpolated_monthly_balance(
                        results[-1],
                        next_year_month(results[-1].year_month),
                        api_models.InterpolationType.inter,
                        monthly_balance,
                        monthly_deposit,
                    )
                )
        results.append(monthly_balances.pop(0))

    monthly_balance_result.monthly_balances = results


def get_interpolated_monthly_balance(
    prev: api_models.MonthlyBalance,
    year_month: str,
    interpolated: api_models.InterpolationType,
    monthly_balance: Decimal = Decimal(0),
    monthly_deposit: Decimal = Decimal(0),
) -> api_models.MonthlyBalance:
    return api_models.MonthlyBalance(
        year_month=year_month,
        start_balance=prev.end_balance,
        monthly_balance=monthly_balance,
        end_balance=prev.end_balance + monthly_balance,
        deposits_to_date=prev.deposits_to_date + monthly_deposit,
        interpolated=interpolated,
    )


def get_num_months_between(start_month_year: str, end_month_year: str) -> int:
    start_year, start_month = map(int, start_month_year.split("-"))
    end_year, end_month = map(int, end_month_year.split("-"))
    result = (end_year - start_year) * 12 + (
        end_month - start_month
    )  # 2024-01 to 2024-02 is 1 month
    # logger.info(f"Months between {start_month_year=} and {end_month_year=} is {result=}")
    return result


def get_interpolated_balance_predict_growth(
    monthly_balances: List[api_models.MonthlyBalance],
    now_year_month: str,
    account_type: api_models.AccountType,
) -> api_models.MonthlyBalance:

    # data needed for all approaches
    first_entry = monthly_balances[0]
    last_entry = monthly_balances[-1]
    months_from_last_data = get_num_months_between(last_entry.year_month, now_year_month)

    total_growth = Decimal(0)
    new_deposits = Decimal(0)

    # assets: diff between first and last valuation divided by months. No predicted deposits.
    if account_type == api_models.AccountType.asset:

        months_between = get_num_months_between(first_entry.year_month, last_entry.year_month)
        growth = last_entry.end_balance - first_entry.end_balance
        growth_per_month = growth / months_between
        total_growth = Decimal(growth_per_month * months_from_last_data)

        logger.info(
            f"{months_from_last_data=}, {months_between=}, {growth=}, {growth_per_month=}, {total_growth=}"
        )
    else:
        recent_growth = []
        for i in range(len(monthly_balances) - 1, 0, -1):
            deposit_this_month = (
                monthly_balances[i].deposits_to_date - monthly_balances[i - 1].deposits_to_date
            )
            growth_this_month = (
                monthly_balances[i].end_balance - deposit_this_month
            ) / monthly_balances[i - 1].end_balance
            recent_growth.append(growth_this_month)
            if len(recent_growth) >= 12:
                break
        ave_growth = statistics.mean(recent_growth)
        # use the last entry to determine if contributions are still being made
        contribs_per_month = (
            monthly_balances[-1].deposits_to_date - monthly_balances[-2].deposits_to_date
        )

        logger.info(f"{months_from_last_data=}, {ave_growth=}, {contribs_per_month=}")

        cur_balance = last_entry.end_balance
        for _ in range(months_from_last_data):
            total_growth += (cur_balance * ave_growth) - cur_balance
            new_deposits += contribs_per_month
            cur_balance += total_growth
            logger.info(f"{total_growth=}, {new_deposits=}, {cur_balance=}")

    return api_models.MonthlyBalance(
        year_month=now_year_month,
        start_balance=last_entry.end_balance,
        monthly_balance=total_growth,
        end_balance=last_entry.end_balance + total_growth,
        deposits_to_date=last_entry.deposits_to_date + new_deposits,
        interpolated=api_models.InterpolationType.end,
    )


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
    as_db_model: bool = False,
) -> Union[List[api_models.TransactionRule], List[db_models.TransactionRule]]:
    query = db_session.query(db_models.TransactionRule)

    if account_ids is not None:
        query = query.filter(db_models.TransactionRule.account_id.in_(account_ids))

    results = query.all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No rules found for {account_ids=}"
        )

    if as_db_model:
        return results
    return [api_models.TransactionRule.model_validate(result) for result in results]


def run_rules(db_session: Session, account_ids: Optional[List[int]] = None):
    rules: List[api_models.TransactionRule] = get_rules(
        db_session=db_session, account_ids=account_ids
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


def add_data_series(
    db_session: Session,
    values: List[api_models.DataSeriesCreate],
) -> api_models.AddDataSeriesResult:
    new_data_series = [db_models.DataSeries(**value.model_dump()) for value in values]

    try:
        db_session.add_all(new_data_series)
        db_session.commit()
    except Exception as ex:
        logger.error(f"Error adding data series: {ex}")
        db_session.rollback()
        raise

    return api_models.AddDataSeriesResult(values_added=len(new_data_series))


def get_data_series(
    db_session: Session,
    keys: Optional[List[str]] = None,
    as_db_model: bool = False,
) -> Union[List[api_models.DataSeries], List[db_models.DataSeries]]:
    query = db_session.query(db_models.DataSeries)

    if keys:
        query = query.filter(db_models.DataSeries.key.in_(keys))

    results = query.all()

    if as_db_model:
        return results

    return [api_models.DataSeries.model_validate(result) for result in results]

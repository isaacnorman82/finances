import logging
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, getcontext
from typing import Dict, List, Optional, Union

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend import api_models, db_models
from backend.balance_interpolation import (
    extend_monthly_balances_to_now,
    fill_missing_months,
)
from backend.util import Timer

logger = logging.getLogger(__name__)


getcontext().prec = 28


def two_dp(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_date_to_month(dt: datetime) -> datetime:
    return datetime(year=dt.year, month=dt.month, day=1)


def get_account(account_id: int, db_session: Session) -> Optional[db_models.Account]:
    return db_session.query(db_models.Account).get(account_id)


def get_accounts(
    db_session: Session,
    institution: Optional[str] = None,
    name: Optional[str] = None,
    as_db_model: bool = False,
) -> List[api_models.Account]:
    query = db_session.query(db_models.Account)

    if institution:
        query = query.filter(db_models.Account.institution == institution)
    if name:
        query = query.filter(db_models.Account.name == name)

    results = query.all()
    if as_db_model:
        return results
    return [api_models.Account.model_validate(result) for result in results]


def create_accounts(
    db_session: Session,
    accounts: Union[api_models.Account, List[api_models.Account]],
    as_db_model: bool = False,
) -> List[Union[api_models.Account, db_models.Account]]:
    if not isinstance(accounts, list):
        accounts = [accounts]

    if len(accounts) == 0:
        return []

    new_accounts: List[db_models.Account] = [
        db_models.Account(**account.model_dump()) for account in accounts
    ]
    db_session.add_all(new_accounts)
    db_session.commit()
    for new_account in new_accounts:
        db_session.refresh(new_account)

    if not as_db_model:
        return [api_models.Account.model_validate(new_account) for new_account in new_accounts]
    return new_accounts


def get_transactions(
    db_session: Session,
    account_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    as_db_model: bool = False,
) -> List[db_models.Transaction] | List[api_models.Transaction]:

    query = db_session.query(db_models.Transaction).filter(
        db_models.Transaction.account_id == account_id
    )

    if start_date:
        query = query.filter(db_models.Transaction.date_time >= start_date)

    if end_date:
        query = query.filter(db_models.Transaction.date_time <= end_date)

    query = query.order_by(db_models.Transaction.date_time.asc())

    # logger.info(str(query.statement.compile(compile_kwargs={"literal_binds": True})))

    results = query.all()

    if as_db_model:
        return results
    return [api_models.Transaction.model_validate(result) for result in results]


def create_transactions(
    db_session: Session,
    transactions: Union[api_models.TransactionCreate, List[api_models.TransactionCreate]],
    as_db_model: bool = False,
) -> List[Union[api_models.Transaction, db_models.Transaction]]:
    if not isinstance(transactions, list):
        transactions = [transactions]

    if len(transactions) == 0:
        return []

    new_transactions: List[db_models.Transaction] = [
        db_models.Transaction(**transaction.model_dump()) for transaction in transactions
    ]
    db_session.add_all(new_transactions)
    db_session.commit()

    # make a list of all account_ids we've added transactions for
    account_ids = list({transaction.account_id for transaction in new_transactions})

    # todo switch uses of list to set where we're passing optional id sets.
    run_rules(db_session, account_ids)

    if not as_db_model:
        return [
            api_models.Transaction.model_validate(new_transaction)
            for new_transaction in new_transactions
        ]
    return new_transactions


def get_last_transaction_dates(
    db_session: Session, account_ids: Optional[List[int]] = None
) -> Dict[int, datetime]:
    # Start the query to get the last transaction date for each account_id
    query = db_session.query(
        db_models.Transaction.account_id, func.max(db_models.Transaction.date_time)
    ).group_by(db_models.Transaction.account_id)

    if account_ids:
        query = query.filter(db_models.Transaction.account_id.in_(account_ids))

    results = query.all()

    # Convert the results to a dictionary
    account_last_transaction_date = {account_id: last_date for account_id, last_date in results}

    return account_last_transaction_date


def get_balance(
    db_session: Session,
    account_ids: Optional[List[int]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[api_models.BalanceResult]:
    results = []

    # Base queries
    balance_query = db_session.query(
        db_models.Transaction.account_id, func.sum(db_models.Transaction.amount).label("balance")
    )
    deposits_query = db_session.query(
        db_models.Transaction.account_id,
        func.sum(db_models.Transaction.amount).label("deposits_to_date"),
    ).filter(db_models.Transaction.is_value_adjustment == False)
    max_date_query = db_session.query(
        db_models.Transaction.account_id,
        func.max(db_models.Transaction.date_time).label("last_transaction_date"),
    )

    # Apply filters
    if account_ids:
        balance_query = balance_query.filter(db_models.Transaction.account_id.in_(account_ids))
        deposits_query = deposits_query.filter(db_models.Transaction.account_id.in_(account_ids))
        max_date_query = max_date_query.filter(db_models.Transaction.account_id.in_(account_ids))
    if start_date:
        balance_query = balance_query.filter(db_models.Transaction.date_time >= start_date)
        deposits_query = deposits_query.filter(db_models.Transaction.date_time >= start_date)
        max_date_query = max_date_query.filter(db_models.Transaction.date_time >= start_date)
    if end_date:
        balance_query = balance_query.filter(db_models.Transaction.date_time <= end_date)
        deposits_query = deposits_query.filter(db_models.Transaction.date_time <= end_date)
        max_date_query = max_date_query.filter(db_models.Transaction.date_time <= end_date)

    # Group by account ID
    balance_query = balance_query.group_by(db_models.Transaction.account_id)
    deposits_query = deposits_query.group_by(db_models.Transaction.account_id)
    max_date_query = max_date_query.group_by(db_models.Transaction.account_id)

    # Execute the queries
    balance_results = {row.account_id: row.balance for row in balance_query.all()}
    deposits_results = {row.account_id: row.deposits_to_date for row in deposits_query.all()}
    max_date_results = {row.account_id: row.last_transaction_date for row in max_date_query.all()}

    all_account_ids = account_ids or list(balance_results.keys())

    for account_id in all_account_ids:
        balance = balance_results.get(account_id, Decimal(0))
        deposits_to_date = deposits_results.get(account_id, Decimal(0))
        last_transaction_date = max_date_results.get(account_id)
        results.append(
            api_models.BalanceResult(
                account_id=account_id,
                balance=balance,
                deposits_to_date=deposits_to_date,
                last_transaction_date=last_transaction_date,
                start_date=start_date,
                end_date=end_date,
            )
        )

    return results


def set_balance(
    db_session: Session,
    account_id: int,
    balance: Decimal,
    deposits_to_date: Optional[Decimal] = None,
    year_month: Optional[datetime] = None,
) -> List[api_models.Transaction]:

    if year_month is None:
        year_month = datetime.now(timezone.utc)

    balance = two_dp(balance)
    year_month = round_date_to_month(year_month)  # Ensures month is set correctly

    # Get current balance and contributions
    current_balance_result = get_balance(db_session, account_ids=[account_id], end_date=year_month)[
        0
    ]
    current_balance = current_balance_result.balance
    current_contributions = current_balance_result.deposits_to_date

    contribution_adjustment = (
        (deposits_to_date - current_contributions) if deposits_to_date is not None else Decimal(0)
    )

    # need to work out balance_adjustment after contribution_adjustment so they don't double contribute
    balance_adjustment = balance - (current_balance + contribution_adjustment)

    # No adjustment needed if both balance and contributions match
    if balance_adjustment == 0 and contribution_adjustment == 0:
        logger.info(
            f"Balance and contributions already set to {balance} and {current_contributions} for {year_month}"
        )
        return []

    transactions = []

    if deposits_to_date == None:
        # if deposits_to_date is None it means we're doing a simple balance set
        desc_type = "Balance"
        trans_type = "set-balance"
    else:
        # we would set is_value_adjustment to true, but the rules currently overwrite
        # to false unless the trans type matches, so for now it's easier to just set the trans type
        # however we should fix it so is_value_adjustment is honoured
        desc_type = "Value"
        trans_type = "Value Adjustment"

    # Adjust for contributions if deposits_to_date is provided and differs from current
    if contribution_adjustment != 0:
        transactions.append(
            api_models.TransactionCreate(
                account_id=account_id,
                date_time=year_month,
                amount=contribution_adjustment,
                transaction_type="Deposit",
                description=f"Contribution adjustment to set total contributions to {deposits_to_date}",
                is_value_adjustment=False,
            )
        )

    # Adjust for balance
    if balance_adjustment != 0:
        transactions.append(
            api_models.TransactionCreate(
                account_id=account_id,
                date_time=year_month,
                amount=balance_adjustment,
                transaction_type=trans_type,
                description=f"{desc_type} adjustment to set balance to {balance}",
                is_value_adjustment=False,
            )
        )

    logger.info(transactions)

    # Handle adjustment in next month if this is not the most recent month
    last_transaction_month = round_date_to_month(
        get_last_transaction_dates(db_session, account_ids=[account_id]).get(account_id, year_month)
    )
    if last_transaction_month > year_month:
        if contribution_adjustment != 0:
            transactions.append(
                api_models.TransactionCreate(
                    account_id=account_id,
                    date_time=year_month + relativedelta(months=1),
                    amount=-contribution_adjustment,
                    transaction_type="Deposit",
                    description="Undo previous month contribution adjustment",
                    is_value_adjustment=False,
                )
            )
        if balance_adjustment != 0:
            transactions.append(
                api_models.TransactionCreate(
                    account_id=account_id,
                    date_time=year_month + relativedelta(months=1),
                    amount=-balance_adjustment,
                    transaction_type=trans_type,
                    description=f"Undo previous month {desc_type} adjustment",
                    is_value_adjustment=False,
                )
            )

    # Create transactions in the database
    results = create_transactions(db_session, transactions)
    return results


def get_first_day_of_next_month(date: datetime) -> datetime:
    next_month = date.replace(day=28) + timedelta(days=4)  # this will never fail
    return next_month.replace(day=1)


def get_account_ids_without_transactions(
    db_session: Session, account_ids: Optional[List[int]] = None
) -> List[int]:
    query = (
        db_session.query(db_models.Account.id)
        .outerjoin(db_models.Transaction)
        .filter(db_models.Transaction.id == None)
    )

    if account_ids:
        query = query.filter(db_models.Account.id.in_(account_ids))

    result = query.all()
    account_ids_without_transactions = [row[0] for row in result]

    return account_ids_without_transactions


def get_monthly_balances(
    db_session: Session, account_ids: Optional[List[int]] = None, interpolate: bool = True
) -> List[api_models.MonthlyBalanceResult]:

    # Prepare the SQL text query
    sql_query = """
        SELECT
            account_id,
            DATE_TRUNC('month', date_time) AS month,
            CAST(SUM(amount) AS DECIMAL) AS monthly_balance,
            CAST(SUM(SUM(amount)) OVER (
                PARTITION BY account_id
                ORDER BY DATE_TRUNC('month', date_time)
            ) AS DECIMAL) AS cumulative_balance,
            CAST(SUM(CASE WHEN is_value_adjustment THEN 0 ELSE amount END) AS DECIMAL) AS monthly_deposit,
            CAST(SUM(SUM(CASE WHEN is_value_adjustment THEN 0 ELSE amount END)) OVER (
                PARTITION BY account_id
                ORDER BY DATE_TRUNC('month', date_time)
            ) AS DECIMAL) AS cumulative_deposits
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
            )
        else:
            previous_month_balance = results[account_id].monthly_balances[-1].end_balance
            start_balance = previous_month_balance

        monthly_balance = Decimal(row[2])
        end_balance = start_balance + monthly_balance

        # Adjust deposits_to_date to reflect cumulative deposits considering negative amounts (withdrawals)
        deposits_to_date = Decimal(row[5])

        monthly_balance_obj = api_models.MonthlyBalance(
            year_month=year_month_str,
            start_balance=start_balance,
            monthly_balance=monthly_balance,
            end_balance=end_balance,
            deposits_to_date=deposits_to_date,
        )

        results[account_id].monthly_balances.append(monthly_balance_obj)

    # Get the account objects
    accounts = get_accounts(db_session)

    if interpolate:
        # Fill in the missing months where there were no transactions
        for account_id, result in results.items():
            account = next(account for account in accounts if account.id == account_id)

            try:
                # Add a final value to the current date for accounts we don't have up-to-date data for
                extend_monthly_balances_to_now(account, result)
            except Exception as ex:
                logger.error(f"Interpolation Error: Failed to extend {account_id=} to now.  {ex=}")

            try:
                # Gap fill to ensure we have data for all months up to the current month
                fill_missing_months(account, result)
            except Exception as ex:
                logger.error(f"Interpolation Error: Failed to gap fill {account_id=}.  {ex=}")

    # Find accounts with no transactions
    empty_accounts = get_account_ids_without_transactions(
        db_session=db_session, account_ids=account_ids
    )

    for account_id in empty_accounts:
        # Add an empty monthly balance so we don't have to make monthly_balances optional
        results[account_id] = api_models.MonthlyBalanceResult(
            account_id=account_id,
            monthly_balances=[
                api_models.MonthlyBalance(
                    year_month=datetime.now().strftime("%Y-%m"),
                    start_balance=Decimal(0),
                    monthly_balance=Decimal(0),
                    end_balance=Decimal(0),
                    deposits_to_date=Decimal(0),
                )
            ],
        )

    # Sort by earliest start date
    results = dict(sorted(results.items(), key=lambda item: item[1].start_year_month))

    return list(results.values())


# todo split this file up


def create_transaction_rules(
    db_session: Session,
    rules: Union[api_models.TransactionRuleCreate, List[api_models.TransactionRuleCreate]],
    as_db_model: bool = False,
) -> List[Union[api_models.TransactionRule, db_models.TransactionRule]]:
    if not isinstance(rules, list):
        rules = [rules]

    if len(rules) == 0:
        return []

    new_rules: List[db_models.TransactionRule] = [
        db_models.TransactionRule(**rule.model_dump()) for rule in rules
    ]
    db_session.add_all(new_rules)
    db_session.commit()

    if not as_db_model:
        return [api_models.TransactionRule.model_validate(new_rule) for new_rule in new_rules]
    return new_rules


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

    # if not results:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail=f"No rules found for {account_ids=}"
    #     )

    if as_db_model:
        return results
    return [api_models.TransactionRule.model_validate(result) for result in results]


# todo all these optional lists should be sets
def run_rules(db_session: Session, account_ids: Optional[Union[int, List[int]]] = None):
    logger.info(f"Running rules, {account_ids=}")

    if account_ids is not None and not isinstance(account_ids, list):
        account_ids = [account_ids]

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
        # logger.error(f"Error running rules: {e}")
        db_session.rollback()
        raise

    # logger.info(f"Rules run.")


def create_data_series(
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


def get_account_backup(db_session: Session) -> api_models.BackupV1:
    db_accounts = get_accounts(db_session=db_session, as_db_model=True)
    api_rules = get_rules(db_session=db_session)

    backup = api_models.BackupV1()

    backup.data_series = [
        api_models.DataSeriesCreate.model_validate(ds)
        for ds in get_data_series(db_session=db_session, as_db_model=True)
    ]

    for db_account in db_accounts:
        db_txs: List[db_models.Transaction] = get_transactions(
            db_session=db_session, account_id=db_account.id, as_db_model=True
        )

        conditions: List[api_models.RuleCondition] = [
            rule.condition for rule in api_rules if rule.account_id == db_account.id
        ]

        transactions: List[api_models.TransactionCreate] = [
            api_models.TransactionCreate.model_validate(tx) for tx in db_txs
        ]
        # this will leave transactions with the account_id field set but we'll overwrite that on import

        backup.accounts.append(
            api_models.AccountBackup(
                account=api_models.AccountCreate.model_validate(db_account),
                rule_conditions=conditions,
                transactions=transactions,
            )
        )
    return backup


def restore_account_backup(db_session: Session, backup: api_models.BackupV1):
    # assume caller already checked db is empty

    # could accept different versions here and upgrade, just handle v1 for now

    create_data_series(db_session=db_session, values=backup.data_series)
    accounts_to_create = [account_backup.account for account_backup in backup.accounts]
    new_accounts = create_accounts(db_session=db_session, accounts=accounts_to_create)

    for new_account, account_backup in zip(new_accounts, backup.accounts):
        rules = [
            api_models.TransactionRuleCreate(account_id=new_account.id, condition=val)
            for val in account_backup.rule_conditions
        ]
        create_transaction_rules(db_session=db_session, rules=rules)

        transactions_to_create = [
            db_models.Transaction(
                account_id=new_account.id, **transaction.model_dump(exclude={"account_id"})
            )
            for transaction in account_backup.transactions
        ]

        db_session.add_all(transactions_to_create)
    db_session.commit()

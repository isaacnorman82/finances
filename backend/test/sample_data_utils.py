import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from backend.api_models import (
    AccountCreate,
    AccountType,
    DataSeriesCreate,
    IngestType,
    IsValueAdjContainsAny,
    RuleCondition,
    TransactionCreate,
    TransactionRuleCreate,
)
from backend.crud import two_dp


def random_date_month(dt):
    first_day = dt.replace(day=1)
    next_month = first_day.replace(month=dt.month % 12 + 1, day=1)
    last_day = next_month - timedelta(days=1)
    random_day = random.randint(1, last_day.day)
    return dt.replace(day=random_day, hour=0, minute=0, second=0, microsecond=0)


class AccountSpec(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime = datetime.now()
    institution: str
    name: str
    description: str | None = None
    account_type: AccountType
    default_ingest_type: IngestType
    is_active: bool
    ac_number: str | None = None
    external_link: str | None = None
    contributions: Decimal | None = None
    monthly_withdrawals_max: Decimal | None = None
    monthly_withdrawals_min: Decimal | None = None
    growth_factor_max: Decimal | None = None
    growth_factor_min: Decimal | None = None
    value: Decimal | None = Decimal("0.00")
    conditions: List[RuleCondition] = []


VALUE_AND_CONTRIB_CONDITION = IsValueAdjContainsAny(
    values=["value adjustment"],
    read_col="transaction_type",
)


ACCOUNT_SPECS = [
    AccountSpec(
        id=1,
        institution="Nationwide",
        name="Current Account",
        account_type=AccountType.current_credit,
        default_ingest_type=IngestType.ofx_transactions,
        is_active=True,
        ac_number="31334345",
        external_link="https://onlinebanking.nationwide.co.uk/AccountList",
        start_date=datetime(2014, 1, 1),
        contributions=Decimal("3540.00"),
        monthly_withdrawals_max=Decimal("-3800.00"),
        monthly_withdrawals_min=Decimal("-2800.00"),
    ),
    AccountSpec(
        id=2,
        institution="Amex",
        name="Credit Card",
        account_type=AccountType.current_credit,
        default_ingest_type=IngestType.csv,
        is_active=True,
        ac_number="8462 9832 3272 1279",
        external_link="https://www.americanexpress.com/en-gb/account/login",
        start_date=datetime(2014, 1, 1),
        monthly_withdrawals_max=Decimal("-1000.00"),
        monthly_withdrawals_min=Decimal("-100.00"),
    ),
    AccountSpec(
        id=3,
        institution="Aviva",
        name="Acme Retirement Plan",
        description="Company pension at Acme",
        account_type=AccountType.pensions,
        default_ingest_type=IngestType.value_and_contrib_csv,
        is_active=True,
        start_date=datetime(2015, 1, 1),
        contributions=Decimal("658.00"),
        growth_factor_max=Decimal("1.006"),
        growth_factor_min=Decimal("0.999"),
        conditions=[VALUE_AND_CONTRIB_CONDITION],
    ),
    AccountSpec(
        id=4,
        institution="Property",
        name="221b Baker Street",
        account_type=AccountType.asset,
        default_ingest_type=IngestType.value_and_contrib_csv,
        is_active=True,
        start_date=datetime(2016, 1, 1),
        contributions=Decimal("271821.00"),
        growth_factor_max=Decimal("1.005"),
        growth_factor_min=Decimal("0.999"),
        value=Decimal("217000.00"),
        conditions=[VALUE_AND_CONTRIB_CONDITION],
    ),
    AccountSpec(
        id=5,
        institution="HSBC",
        name="Mortgage",
        description="Mortgage on 221b Baker Street",
        account_type=AccountType.loans,
        default_ingest_type=IngestType.value_and_contrib_csv,
        is_active=True,
        start_date=datetime(2016, 1, 1),
        contributions=Decimal("800.00"),
        growth_factor_max=Decimal("1.001"),
        growth_factor_min=Decimal("1.001"),
        value=Decimal("-207000.00"),
    ),
    AccountSpec(
        id=6,
        institution="MoneyFarm",
        name="IF-ISA",
        account_type=AccountType.savings,
        default_ingest_type=IngestType.value_and_contrib_csv,
        is_active=True,
        start_date=datetime(2014, 3, 1),
        contributions=Decimal("100.00"),
        growth_factor_max=Decimal("1.005"),
        growth_factor_min=Decimal("0.998"),
        conditions=[VALUE_AND_CONTRIB_CONDITION],
    ),
]

SAVING_SPEC = next(spec for spec in ACCOUNT_SPECS if spec.account_type == AccountType.savings)


def create_tax_data_series():
    random.seed(2001)
    dt = datetime(2015, 1, 1)
    tax_paid = Decimal("26789.12")
    salary = two_dp(tax_paid * 3)

    results = []

    while dt < datetime.now():
        results.append(DataSeriesCreate(date_time=dt, key="Tax Paid", value=str(tax_paid)))
        net_pay = two_dp(tax_paid * random_between(1.9, 2.2))
        results.append(DataSeriesCreate(date_time=dt, key="Net Pay", value=str(net_pay)))
        tax_paid *= random_between(0.95, 1.15)

        results.append(DataSeriesCreate(date_time=dt, key="Salary", value=str(salary)))
        bonus_target = two_dp(salary * Decimal(0.15))
        results.append(DataSeriesCreate(date_time=dt, key="Bonus Target", value=str(bonus_target)))
        salary *= random_between(1, 1.15)
        dt += relativedelta(years=1)

    results.append(DataSeriesCreate(date_time=datetime(2015, 1, 1), key="Company", value="Acme"))
    results.append(
        DataSeriesCreate(date_time=datetime(2018, 1, 1), key="Company", value="Weyland Yutani")
    )
    results.append(
        DataSeriesCreate(date_time=datetime(2020, 1, 1), key="Company", value="Tyrell Corporation")
    )
    results.append(
        DataSeriesCreate(date_time=datetime(2022, 1, 1), key="Company", value="Nuka Cola")
    )

    return results


def create_sample_accounts():
    return [
        AccountCreate(
            institution=spec.institution,
            name=spec.name,
            account_type=spec.account_type,
            default_ingest_type=spec.default_ingest_type,
            is_active=spec.is_active,
        )
        for spec in ACCOUNT_SPECS
    ]


def create_sample_rules():
    rules = []
    for spec in ACCOUNT_SPECS:
        for condition in spec.conditions:
            rules.append(
                TransactionRuleCreate(
                    account_id=spec.id,
                    condition=condition,
                )
            )
    return rules


def create_sample_transactions():
    random.seed(42)
    transactions: List[TransactionCreate] = []
    for spec in ACCOUNT_SPECS:
        create_sample_transactions_for_account(spec, transactions)
    return transactions


def create_sample_transactions_for_account(
    spec: AccountSpec, transactions: List[TransactionCreate]
):
    dt = spec.start_date

    while dt < spec.end_date:

        create_contribution_tx(spec, dt, transactions)

        if dt == spec.start_date:
            create_initial_value_tx(spec, dt, transactions)
        else:
            create_growth_tx(spec, dt, transactions)

        create_withdrawal_tx(spec, dt, transactions)

        # increase date by one month
        dt = dt + relativedelta(months=1)


def create_initial_value_tx(spec: AccountSpec, dt: datetime, transactions: List[TransactionCreate]):
    if spec.account_type not in [AccountType.asset, AccountType.loans]:
        return

    if not spec.value or not spec.contributions:
        raise ValueError(f"Asset {spec.id} is missing value or contributions")

    match spec.account_type:
        case AccountType.asset:
            transactions.append(
                TransactionCreate(
                    account_id=spec.id,
                    date_time=dt,
                    amount=spec.contributions,
                    transaction_type="Deposit",
                    description="Total Mortgage Contributions",
                )
            )
            transactions.append(
                TransactionCreate(
                    account_id=spec.id,
                    date_time=dt,
                    amount=spec.value - spec.contributions,
                    transaction_type="Value Adjustment",
                    description="Market value",
                )
            )

        case AccountType.loans:
            transactions.append(
                TransactionCreate(
                    account_id=spec.id,
                    date_time=dt,
                    amount=spec.value,
                    transaction_type="Withdrawal",
                    description="Loan drawdown",
                )
            )


def create_contribution_tx(spec: AccountSpec, dt: datetime, transactions: List[TransactionCreate]):
    match spec.account_type:
        case AccountType.current_credit:
            description = "Pay"
            tx_dt = dt.replace(day=26)
            if spec.contributions is None:
                # it's a credit card and we clear the last month each month
                amount = abs(spec.value)
                description = "Clear balance"
            else:
                amount = spec.contributions
        case AccountType.pensions:
            description = "Pension contribution"
            tx_dt = dt.replace(day=1)
            amount = spec.contributions
        case AccountType.loans:
            description = "Loan repayment"
            tx_dt = dt.replace(day=3)
            amount = spec.contributions
        case AccountType.savings:
            description = "Standing Order"
            tx_dt = dt.replace(day=5)
            amount = spec.contributions
        case _:
            return

    spec.value += amount

    transactions.append(
        TransactionCreate(
            account_id=spec.id,
            date_time=tx_dt,
            amount=amount,
            transaction_type="Deposit",
            description=description,
        )
    )


def random_between(min_val: Decimal, max_val: Decimal) -> Decimal:
    return Decimal(random.uniform(float(min_val), float(max_val)))


def create_growth_tx(spec: AccountSpec, dt: datetime, transactions: List[TransactionCreate]):
    if spec.account_type not in [
        AccountType.asset,
        AccountType.pensions,
        AccountType.loans,
        AccountType.savings,
    ]:
        return

    growth_factor = random_between(spec.growth_factor_min, spec.growth_factor_max)
    amount = two_dp((spec.value * growth_factor) - spec.value)
    spec.value += amount

    if spec.account_type == AccountType.loans:
        description = "Loan interest"
    else:
        description = "Market value change"

    if amount > 100000:
        assert "too big"

    transactions.append(
        TransactionCreate(
            account_id=spec.id,
            date_time=dt,
            amount=amount,
            transaction_type="Value Adjustment",
            description=description,
        )
    )


def create_withdrawal_tx(spec: AccountSpec, dt: datetime, transactions: List[TransactionCreate]):
    if spec.account_type != AccountType.current_credit:
        return

    if spec.monthly_withdrawals_max is None or spec.monthly_withdrawals_min is None:
        raise ValueError(f"Current account {spec.id} is missing withdrawal limits")

    num_tx = random.randint(5, 10)

    for _ in range(num_tx):
        amount = two_dp(
            random_between(
                spec.monthly_withdrawals_min / num_tx, spec.monthly_withdrawals_max / num_tx
            )
        )

        transactions.append(
            TransactionCreate(
                account_id=spec.id,
                date_time=random_date_month(dt),
                amount=amount,
                transaction_type="Withdrawal",
                description="Withdrawal",
            )
        )
        spec.value += amount

    if spec.value > 8000:
        amount = Decimal(random.randint(1, 7) * 1000)

        tx_date = random_date_month(dt)

        transactions.append(
            TransactionCreate(
                account_id=spec.id,
                date_time=tx_date,
                amount=-amount,
                transaction_type="Transfer to ISA",
                description="Transfer",
            )
        )
        spec.value -= amount

        transactions.append(
            TransactionCreate(
                account_id=SAVING_SPEC.id,
                date_time=tx_date,
                amount=amount,
                transaction_type="Transfer from current account",
                description="Deposit",
            )
        )
        SAVING_SPEC.value += amount

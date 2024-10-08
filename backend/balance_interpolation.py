import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, getcontext
from statistics import mean, median
from typing import List, Tuple

from backend.api_models import (
    Account,
    AccountType,
    InterpolationType,
    MonthlyBalance,
    MonthlyBalanceResult,
)

logger = logging.getLogger(__name__)

getcontext().prec = 28

ACCOUNT_TYPES_WITH_GROWTH = [AccountType.pensions, AccountType.savings, AccountType.asset]


def extend_monthly_balances_to_now(account: Account, result: MonthlyBalanceResult):
    if not account.is_active:
        return  # only extend active accounts

    now_year_month: str = datetime.now().strftime("%Y-%m")
    if result.end_year_month == now_year_month:
        return  # nothing to do

    latest_balance: MonthlyBalance = result.monthly_balances[-1]
    additional_balance: Decimal = Decimal(0)
    additional_deposits: Decimal = Decimal(0)
    if account.account_type in ACCOUNT_TYPES_WITH_GROWTH:
        try:
            median_growth_factor, median_monthly_deposit = calculate_growth_factor_for_account(
                result.monthly_balances
            )

            months = get_num_months_between(latest_balance.year_month, now_year_month)
            target_end_balance: Decimal = calculate_balance_after_growth(
                latest_balance.end_balance, median_growth_factor, months
            )
            additional_balance = target_end_balance - latest_balance.end_balance
            additional_deposits = median_monthly_deposit * months
            # logger.info(
            #     f"Extending {account.id} - {account.name}: {months=},{median_growth_factor=}, {median_monthly_deposit=}, {target_end_balance=}, {additional_balance=}, {additional_deposits=}"
            # )
        except ValueError as e:
            logging.warning(f"Error calculating growth factor for account {account.id}: {e}")

    result.monthly_balances.append(
        create_interpolated_mb(
            prev=latest_balance,
            year_month=now_year_month,
            interpolated=InterpolationType.end,
            additional_balance=additional_balance,
            additional_deposits=additional_deposits,
        )
    )


def fill_gap_in_non_growth_account(
    current_mb: MonthlyBalance,
    next_mb: MonthlyBalance,
    gap_months: int,
    updated_balances: List[MonthlyBalance],
):
    if gap_months <= 0:
        return  # No gap to fill

    for _ in range(1, gap_months):
        new_year_month = next_year_month(current_mb.year_month)
        interpolated_mb = create_interpolated_mb(
            prev=current_mb, year_month=new_year_month, interpolated=InterpolationType.inter
        )
        updated_balances.append(interpolated_mb)
        current_mb = interpolated_mb  # Update current for the next iteration

    # Update the next non-interpolated entry
    next_mb.start_balance = updated_balances[-1].end_balance
    next_mb.monthly_balance = next_mb.end_balance - next_mb.start_balance

    # logging.info(f"Basic gap fill completed.")


def fill_gap_in_growth_account(
    current_mb: MonthlyBalance,
    next_mb: MonthlyBalance,
    gap_months: int,
    updated_balances: List[MonthlyBalance],
):
    if gap_months <= 0:
        logging.warning("Ended up in fill_gap_in_growth_account with no gap to fill.")
        return

    deposits_between = next_mb.deposits_to_date - current_mb.deposits_to_date
    monthly_deposit = deposits_between / gap_months

    growth_factor = calculate_monthly_growth_factor(
        start_amount=current_mb.end_balance,
        end_amount=next_mb.end_balance,
        deposits_between=deposits_between,
        months=gap_months,
    )

    # if there's no growth treat as non-growth gap.
    # mostly the same but also doesn't interpolate monthly deposits
    if growth_factor == 1:
        fill_gap_in_non_growth_account(current_mb, next_mb, gap_months, updated_balances)
        return

    # logger.info(f"fill_gap_in_growth_account {gap_months=} {growth_factor=} {monthly_deposit=}")

    for _ in range(1, gap_months):
        new_year_month = next_year_month(current_mb.year_month)
        balance_from_growth = (current_mb.end_balance * growth_factor) - current_mb.end_balance
        additional_balance = balance_from_growth + monthly_deposit
        additional_deposits = monthly_deposit

        interpolated_mb = create_interpolated_mb(
            prev=current_mb,
            year_month=new_year_month,
            interpolated=InterpolationType.inter,
            additional_balance=additional_balance,
            additional_deposits=additional_deposits,
        )
        updated_balances.append(interpolated_mb)
        current_mb = interpolated_mb  # Update current for the next iteration

    # Update the next non-interpolated entry
    next_mb.start_balance = updated_balances[-1].end_balance
    next_mb.monthly_balance = next_mb.end_balance - next_mb.start_balance
    # next_mb.deposits_to_date = updated_balances[-1].deposits_to_date

    # logging.info(f"Gap fill completed {growth_factor=} {monthly_deposit=}")


def fill_missing_months(account: Account, result: MonthlyBalanceResult):
    monthly_balances = result.monthly_balances
    updated_balances = []

    for i in range(len(monthly_balances) - 1):
        current_mb = monthly_balances[i]
        next_mb = monthly_balances[i + 1]

        # Add the current month balance to the updated list
        updated_balances.append(current_mb)

        # Calculate the gap in months between the current and next month
        gap_months = get_num_months_between(current_mb.year_month, next_mb.year_month)

        if gap_months > 1:
            # logging.info(
            #     f"Filling Gap in Account {account.id} - {account.name} of {gap_months} months between {current_mb.year_month} and {next_mb.year_month}"
            # )
            if account.account_type in ACCOUNT_TYPES_WITH_GROWTH:
                fill_gap_in_growth_account(current_mb, next_mb, gap_months, updated_balances)
            else:
                fill_gap_in_non_growth_account(current_mb, next_mb, gap_months, updated_balances)

    # Add the final balance after processing all gaps
    final_mb = monthly_balances[-1]
    updated_balances.append(final_mb)

    # Update the result with the newly interpolated monthly balances
    result.monthly_balances = updated_balances


# helper functions
# todo default year_month to None and then set to next_year_month(prev) and default type to inter
def create_interpolated_mb(
    prev: MonthlyBalance,
    year_month: str,
    interpolated: InterpolationType,
    additional_balance: Decimal = Decimal(0),
    additional_deposits: Decimal = Decimal(0),
) -> MonthlyBalance:
    return MonthlyBalance(
        year_month=year_month,
        start_balance=quantize_decimal(prev.end_balance),
        monthly_balance=quantize_decimal(additional_balance),
        end_balance=quantize_decimal(prev.end_balance + additional_balance),
        deposits_to_date=quantize_decimal(prev.deposits_to_date + additional_deposits),
        interpolated=interpolated,
    )


def quantize_decimal(value: Decimal, decimal_places: int = 2) -> Decimal:
    return value.quantize(Decimal("1." + "0" * decimal_places), rounding=ROUND_HALF_UP)


def calculate_growth_factor_for_account(
    monthly_balances: List[MonthlyBalance], max_sample_size: int = 12
) -> Tuple[Decimal, Decimal]:
    # Filter out balances with InterpolationType.none
    filtered_balances = [mb for mb in monthly_balances if mb.interpolated == InterpolationType.none]

    # Sort balances by year_month in ascending order and limit to max_sample_size
    filtered_balances.sort(key=lambda mb: mb.year_month)
    filtered_balances = filtered_balances[
        -max_sample_size:
    ]  # Keep the last max_sample_size entries

    if len(filtered_balances) < 2:
        raise ValueError("Not enough data points to calculate growth factors")

    # Calculate monthly growth factors and deposits
    growth_factors = []
    monthly_deposits = []

    for i in range(len(filtered_balances) - 1, 0, -1):
        deposit_this_month = (
            filtered_balances[i].deposits_to_date - filtered_balances[i - 1].deposits_to_date
        )

        start_amount = filtered_balances[i - 1].end_balance
        end_amount = filtered_balances[i].end_balance

        num_months = get_num_months_between(
            filtered_balances[i - 1].year_month, filtered_balances[i].year_month
        )

        growth_factor = calculate_monthly_growth_factor(
            start_amount, end_amount, deposit_this_month, Decimal(num_months)
        )
        growth_factors.append(growth_factor)
        monthly_deposits.append(deposit_this_month)

    # logger.info(f"{growth_factors=} {monthly_deposits=}")
    median_growth_factor = Decimal(median(growth_factors))

    if (
        len(monthly_deposits) < (max_sample_size / 2)
        or monthly_balances[0].deposits_to_date == monthly_balances[-1].deposits_to_date
    ):
        # if we don't have half the sample size or no proof deposits happened after the first month, set to zero
        # logger.info("Setting median_monthly_deposit to zero")
        median_monthly_deposit = Decimal(0)
    else:
        median_monthly_deposit = Decimal(median(monthly_deposits))

    return median_growth_factor, median_monthly_deposit


def calculate_monthly_growth_factor(
    start_amount: Decimal,
    end_amount: Decimal,
    deposits_between: Decimal = Decimal(0),
    months: Decimal = Decimal(1),
):
    if start_amount == 0 or months == 0:
        return Decimal(1.0)
    else:
        return ((end_amount - deposits_between) / start_amount) ** (Decimal(1) / months)


def calculate_balance_after_growth(
    start_amount: Decimal, growth_factor: Decimal, months: int
) -> Decimal:
    end_amount = start_amount * (growth_factor**months)
    return quantize_decimal(end_amount)


def get_num_months_between(start_month_year: str, end_month_year: str) -> int:
    start_year, start_month = map(int, start_month_year.split("-"))
    end_year, end_month = map(int, end_month_year.split("-"))
    result = (end_year - start_year) * 12 + (
        end_month - start_month
    )  # 2024-01 to 2024-02 is 1 month
    return result


def next_year_month(year_month: str) -> str:
    year, month = map(int, year_month.split("-"))
    month = (month % 12) + 1
    if month == 1:
        year += 1
    return f"{year:04d}-{month:02d}"

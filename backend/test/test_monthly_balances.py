from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.api_models import AccountSummary
from backend.main import app

client = TestClient(app)


@pytest.mark.usefixtures("insert_sample_accounts_and_transactions")
def test_account_summaries():
    response = client.get(f"/api/accounts/summary/")
    assert response.status_code == 200

    # convert summaries json to a list of AccountSummary objects
    account_summaries = [AccountSummary.model_validate(val) for val in response.json()]

    # todo setup the db - for now just assume it's populated
    assert len(account_summaries) > 0

    for summary in account_summaries:
        if summary.account.is_active == False:
            assert summary.balance == 0

        assert summary.last_transaction_date is not None

        assert len(summary.monthly_balances.monthly_balances) > 0

        running_balance = Decimal("0.00")
        for monthly_balance in summary.monthly_balances.monthly_balances:
            assert monthly_balance.start_balance == running_balance
            assert running_balance + monthly_balance.monthly_balance == monthly_balance.end_balance

            running_balance += monthly_balance.monthly_balance

        assert running_balance == summary.balance

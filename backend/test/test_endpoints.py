import pytest
from fastapi.testclient import TestClient

from backend.api_models import Account, AccountCreate, IngestType
from backend.main import app

# todo divide into separate files

client = TestClient(app)


@pytest.mark.usefixtures("insert_sample_accounts")
def test_list_accounts(sample_accounts):
    response = client.get(f"/api/accounts/")
    accounts = [Account.model_validate(val) for val in response.json()]
    assert len(accounts) == len(sample_accounts)
    assert response.status_code == 200


def test_create_account(sample_accounts):
    response = client.post(f"/api/accounts/", json=sample_accounts[0].model_dump())
    assert response.status_code == 200


def test_get_account_summary():
    response = client.get(f"/api/accounts/summary/")
    assert response.status_code == 200


@pytest.mark.usefixtures("insert_sample_accounts")
def test_get_account_by_id():
    account_id = 1
    response = client.get(f"/api/accounts/{account_id}/")
    assert response.status_code == 200


def test_list_transactions():
    account_id = 1
    response = client.get(f"/api/accounts/{account_id}/transactions/")
    assert response.status_code == 200


@pytest.mark.skip(reason="Need sample files to test this")
def test_ingest_transactions():
    account_id = 1
    files = {"upload_file": ("testfile.csv", open("testfile.csv", "rb"), "text/csv")}
    response = client.post(f"/api/accounts/{account_id}/transactions/", files=files)
    assert response.status_code == 200


def test_get_account_balance():
    account_id = 1
    response = client.get(f"/api/accounts/{account_id}/balance/")
    assert response.status_code == 200


def test_get_monthly_account_balance():
    response = client.get(f"/api/balance/monthly/")
    assert response.status_code == 200


def test_get_data_series():
    response = client.get(f"/api/dataseries/")
    assert response.status_code == 200


def test_add_data_series_values():
    data_series = {
        "date_time": "2023-01-01T00:00:00Z",
        "key": "example_key",
        "value": "example_value",
    }
    response = client.post(f"/api/dataseries/", json=data_series)
    assert response.status_code == 200

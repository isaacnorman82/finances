from test.conftest import BASE_URL

import httpx
import pytest

# todo divide into separate files and decide how to stub the db


@pytest.mark.asyncio
async def test_list_accounts():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/accounts/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_account():
    account_data = {
        "institution": "Bank A",
        "name": "Checking Account",
        "account_type": "Current/Credit",
        "default_ingest_type": "csv",
        "is_active": True,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/accounts/", json=account_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_account_summary():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/accounts/summary/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_account_by_id():
    account_id = 1
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/accounts/{account_id}/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_transactions():
    account_id = 1
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/accounts/{account_id}/transactions/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ingest_transactions():
    account_id = 1
    files = {"upload_file": ("testfile.csv", open("testfile.csv", "rb"), "text/csv")}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/accounts/{account_id}/transactions/", files=files
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_account_balance():
    account_id = 1
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/accounts/{account_id}/balance/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_monthly_account_balance():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/balance/monthly/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_data_series():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/dataseries/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_data_series_values():
    data_series = {
        "date_time": "2023-01-01T00:00:00Z",
        "key": "example_key",
        "value": "example_value",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/dataseries/", json=data_series)
    assert response.status_code == 200

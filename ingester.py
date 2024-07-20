import argparse
import json
from typing import Optional

import httpx

from app.api_models import Account, AccountCreate


def get_account_id(account: AccountCreate) -> Optional[Account]:
    # use httpx to get the account using the institution and name as query parameters
    response = httpx.get(
        "http://localhost:8000/api/accounts/",
        params={"institution": account.institution, "name": account.name},
    )

    # Raise an exception if the response status code is not 200
    response.raise_for_status()

    results = response.json()
    if len(results) == 0:
        return None

    return Account(**results[0])


def create_account(account: AccountCreate) -> Optional[Account]:
    # Create the account
    response = httpx.post(
        "http://localhost:8000/api/accounts/",
        json=account.model_dump(),
    )
    response.raise_for_status()
    return Account(**response.json())


def post_transactions(account: Account, transaction_file):
    # check file extenstion for csv or ofx
    if transaction_file.name.endswith(".csv"):
        data_type = "text/csv"
    elif transaction_file.name.endswith(".ofx"):
        data_type = "text/xml"
    else:
        raise ValueError("Unsupported file type")

    # Post the transactions
    with open(transaction_file.name, "rb") as f:
        files = {"upload_file": (transaction_file.name, f, data_type)}
        response = httpx.post(
            f"http://localhost:8000/api/accounts/{account.id}/transactions/?ingest_type={account.default_ingest_type}",
            files=files,
        )

    print(response.json())

    response.raise_for_status()


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="CLI for Transaction Ingestion")

    # Add the required arguments
    parser.add_argument(
        "account_file",
        type=argparse.FileType("r"),
        help="Path to a JSON file holding an account.",
    )
    parser.add_argument(
        "transaction_file",
        type=argparse.FileType("r"),
        help="Path to the transaction file to ingest",
    )

    # add optional argument, bool, create account if not found
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create the account if it does not exist",
    )

    # Parse the command line arguments
    args = parser.parse_args()

    account_create = AccountCreate(**json.load(args.account_file))

    # find the account using the json
    account = get_account_id(account_create)

    if not account and args.create:
        account = create_account(account_create)

    if not account:
        print("Account not found and not created")
        return

    # print account object
    print(f"Ingesting to {account.institution} - {account.name} ({account.id})")

    # Post the transactions
    post_transactions(account, args.transaction_file)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

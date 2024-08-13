from backend import crud
from backend.db import SessionLocal
from backend.test.sample_data_utils import (
    create_sample_accounts,
    create_sample_transactions,
    create_tax_data_series,
)

sample_accounts = create_sample_accounts()
sample_transactions = create_sample_transactions()
sample_data_series = create_tax_data_series()

print(
    f"Loading {len(sample_accounts)} sample accounts with {len(sample_transactions)} transactions..."
)

db_session = SessionLocal()

crud.create_accounts(db_session=db_session, accounts=sample_accounts)
crud.create_transactions(db_session=db_session, transactions=sample_transactions)
print("Sample data loaded, loading data series...")
crud.add_data_series(db_session=db_session, values=sample_data_series)

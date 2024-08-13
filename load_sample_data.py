from backend import crud
from backend.db import SessionLocal
from backend.test.sample_data_utils import (
    create_sample_accounts,
    create_sample_rules,
    create_sample_transactions,
    create_tax_data_series,
)

sample_accounts = create_sample_accounts()
sample_rules = create_sample_rules()
sample_transactions = create_sample_transactions()
sample_data_series = create_tax_data_series()

db_session = SessionLocal()

print(f"Adding {len(sample_accounts)} accounts.")
crud.create_accounts(db_session=db_session, accounts=sample_accounts)
print(f"Adding {len(sample_rules)} rules.")
crud.create_transaction_rules(db_session=db_session, rules=sample_rules)
print(f"Adding {len(sample_transactions)} transactions.")
crud.create_transactions(db_session=db_session, transactions=sample_transactions)
print(f"Adding {len(sample_data_series)} data series values.")
crud.add_data_series(db_session=db_session, values=sample_data_series)

import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List

import pytest
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from backend import crud
from backend.db import Base, get_db_session, get_db_url
from backend.main import app
from backend.test.sample_data_utils import (
    create_sample_accounts,
    create_sample_rules,
    create_sample_transactions,
)


@pytest.fixture(scope="session")
def unique_test_db_name(request):
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", "master")
    return f"test_db_{worker_id}_{uuid.uuid4().hex}"


@pytest.fixture(scope="session")
def db_engine(unique_test_db_name):
    base_url = get_db_url()
    test_db_url = f"{base_url}{unique_test_db_name}"

    if not database_exists(test_db_url):
        create_database(test_db_url)

    engine = create_engine(test_db_url)
    yield engine

    engine.dispose()  # Ensure all connections are closed
    drop_database(test_db_url)


@pytest.fixture(scope="function", autouse=True)
def db_session(db_engine):
    """
    Automatically use the db_session fixture in all tests.
    """
    Base.metadata.create_all(bind=db_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()

    yield session

    session.close()  # Ensure session is closed after each test
    Base.metadata.drop_all(bind=db_engine)  # Cleanup tables after each test


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment(db_session):
    """
    Override the FastAPI dependencies to use the test database session.
    """

    def get_db_override():
        yield db_session

    app.dependency_overrides[get_db_session] = get_db_override

    yield  # This allows the fixture to run both at setup and teardown

    app.dependency_overrides.clear()  # Clear overrides after the session


@pytest.fixture(scope="session")
def sample_accounts():
    return create_sample_accounts()


@pytest.fixture(scope="session")
def sample_rules():
    return create_sample_rules()


@pytest.fixture(scope="session")
def sample_transactions():
    return create_sample_transactions()


@pytest.fixture(scope="function")
def insert_sample_accounts(db_session, sample_accounts):
    crud.create_accounts(db_session=db_session, accounts=sample_accounts)


@pytest.fixture(scope="function")
def insert_sample_data(db_session, sample_accounts, sample_rules, sample_transactions):
    crud.create_accounts(db_session=db_session, accounts=sample_accounts)
    crud.create_transaction_rules(db_session=db_session, rules=create_sample_rules)
    crud.create_transactions(db_session=db_session, transactions=sample_transactions)

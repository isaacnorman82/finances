import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
# todo switch to env var and direnv
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@0.0.0.0/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Route Dependency
def get_db_session():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def create_account_summary_view(engine):
    create_view_sql = """
    CREATE OR REPLACE VIEW public.account_summary AS
    SELECT
        CONCAT(a.institution, ' - ', a.name) AS name,
        t.account_id,
        COUNT(*) AS transactions,
        SUM(t.amount) AS balance,
        MIN(t.date_time) AS start_date,
        MAX(t.date_time) AS end_date
    FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    GROUP BY t.account_id, a.institution, a.name
    ORDER BY t.account_id ASC;
    """

    with engine.connect() as connection:
        try:
            connection.execute(text(create_view_sql))
            logger.info(create_view_sql)
            logger.info("View 'account_summary' created or updated successfully.")
        except SQLAlchemyError as e:
            # Catch and handle specific SQLAlchemy errors
            print(f"Error occurred while creating view: {e}")

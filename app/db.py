from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

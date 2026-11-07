import pytest
from sqlalchemy.orm import Session

from app.db import engine
from app.main import app


@pytest.fixture
def db_session():
    """Everything the test writes is rolled back afterwards, even if the code commits."""
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()

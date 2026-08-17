import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# `app.config.get_settings()` is `@lru_cache`d and `app.database.session`
# creates its engine at import time, so DATABASE_URL must be a real (file-based)
# path fixed *before* the first app import anywhere in the test session --
# `sqlite:///:memory:` gives every new connection its own empty database and
# causes "no such table" errors as soon as more than one connection is opened.
_TEST_DB_PATH = Path(tempfile.gettempdir()) / "sentinelchain_test.db"
_TEST_DB_PATH.unlink(missing_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH.as_posix()}")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
import app.models  # noqa: F401


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()

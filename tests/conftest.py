import os

import pytest
from sqlalchemy import create_engine, NullPool
from arxiv.db import Session as arXiv_session
from arxiv.db.models import configure_db_engine
from . import ROOT_DIR
from dotenv import load_dotenv, dotenv_values


@pytest.fixture(scope="module")
def localenv() -> dict:
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
    yield dotenv_values()


@pytest.fixture(scope="function")
def classic_db_engine(localenv: dict):
    db_uri = localenv['CLASSIC_DB_URI']
    conn_args = {}
    db_engine = create_engine(db_uri, connect_args=conn_args, poolclass=NullPool)
    yield db_engine
    db_engine.dispose()

@pytest.fixture
def configured_db(classic_db_engine):
    db_engine, _ = configure_db_engine(classic_db_engine,None)
    yield db_engine
    arXiv_session.remove()

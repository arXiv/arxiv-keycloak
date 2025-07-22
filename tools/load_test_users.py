"""
Load initial test data
"""
import os
import logging
import time
from typing import List, Tuple
import argparse

from sqlalchemy import create_engine, text, inspect, Engine
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError, IntegrityError

from arxiv.auth.legacy.util import bootstrap_arxiv_db
from arxiv.util.database_loader import DatabaseLoader

from load_test_data import instantiate_db_engine

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_test_data(db_engine: Engine) -> None:
    """
    Load the test data

    :param db_engine:
    :return:
    """
    test_data_dir = os.path.join(root_dir, 'tests', 'test-users')

    logger.info(f"test_data_dir: {test_data_dir}")
    # load users
    loader = DatabaseLoader(db_engine)
    users = [os.path.join(test_data_dir, filename) for filename in sorted([fn for fn in os.listdir(test_data_dir) if fn.endswith('.yaml')])]
    logger.info(f"users: {users!r}")
    for user in users:
        try:
            loader.load_data_from_files([user])
        except IntegrityError:
            logger.info(f"pass user: {user!r}")
            pass


def main() -> None:
    """
    Load test users

    :return: None
    """
    db_engine, tables = instantiate_db_engine()

    load_test_data(db_engine)


if __name__ == '__main__':
    #parser = argparse.ArgumentParser(description="Initial load arxvi database")
    #parser.add_argument('--load-test-data', action='store_true', help="Load test data.")
    #args = parser.parse_args()

    main()

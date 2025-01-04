import os
import logging

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool

from arxiv.auth.legacy.util import bootstrap_arxiv_db
from arxiv.util.database_loader import DatabaseLoader

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(create_schema: bool = False):
    db_uri = os.environ.get('CLASSIC_DB_URI')
    if not db_uri:
        logger.error('CLASSIC_DB_URI is not set')
        exit(1)
    conn_args = {"ssl": None}
    db_engine = create_engine(db_uri, connect_args=conn_args, poolclass=NullPool)
    tables = []

    if not create_schema:
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        pass

    if len(tables) == 0 or create_schema:
        # Don't use the db models for mysql. It does not work.
        # create_arxiv_db_schema(db_engine)
        with open(os.path.join(root_dir, "tests", "development", "arxiv_db_schema.sql")) as sql_file:
            sql_script = sql_file.read()

        # Establish a connection from the engine
        with db_engine.connect() as connection:
            try:
                connection.execute(text(sql_script))
                logging.info("SQL file executed successfully!")
            except Exception as exc:
                logger.error(f"Error executing SQL: {exc}")
                raise exc

    test_data_dir = os.path.join(root_dir, "tests", "development", "test-data")
    bootstrap_arxiv_db(db_engine, test_data_dir=test_data_dir)
    logger.info('arxiv db bootstapped')

    test_data_dir = os.path.join(root_dir, 'tests', 'data')

    # load users
    loader = DatabaseLoader(db_engine)
    users = [os.path.join(test_data_dir, filename) for filename in sorted([fn for fn in os.listdir(test_data_dir) if fn.startswith('test-user')])]
    loader.load_data_from_files(users)


if __name__ == '__main__':
    main()

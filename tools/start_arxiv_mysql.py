"""
start_arxiv_mysql.py starts mysql docker and empties/bootstraps the database.

"""
import os
import subprocess
import logging
import sys

from sqlalchemy import create_engine, text, CursorResult, Engine
from sqlalchemy.pool import NullPool
from arxiv.auth.legacy.util import bootstrap_arxiv_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

PYTHON_EXE = "python"
DB_NAME = "testdb"
DB_PORT = "26001"
ROOT_PASSWORD = "rootpassword"

my_sql_cmd = ["mysql", f"--port={DB_PORT}", "-h", "127.0.0.1", "-u", "root", f"--password={ROOT_PASSWORD}"]

def arxiv_base_dir():
    return os.environ.get("ARXIV_BASE_DIR", os.path.expanduser("~/arxiv/arxiv-base"))

def start_clean_mysql() -> Engine:
    conn_args = {}
    loader_py = os.path.join(arxiv_base_dir(), "development", "load_arxiv_db_schema.py")
    arxiv_base_env = os.environ.copy()
    python_path = [arxiv_base_dir()] + sys.path
    arxiv_base_env['PYTHONPATH'] = ":".join(python_path)
    subprocess.run(["poetry", "run", PYTHON_EXE, loader_py, f"--db_name={DB_NAME}", f"--db_port={DB_PORT}",
                   f"--root_password={ROOT_PASSWORD}"], encoding="utf-8", check=True, env=arxiv_base_env)
    db_uri = f"mysql://testuser:testpassword@127.0.0.1:{DB_PORT}/{DB_NAME}"
    use_ssl = False
    if not use_ssl:
        conn_args["ssl"] = None
    db_engine = create_engine(db_uri, connect_args=conn_args, poolclass=NullPool)

    # Clean up the tables to real fresh
    targets = []
    with db_engine.connect() as connection:
        tables = [row[0] for row in connection.execute(text("SHOW TABLES"))]
        for table_name in tables:
            counter: CursorResult = connection.execute(text(f"select count(*) from {table_name}"))
            count = counter.first()[0]
            if count and int(count):
                targets.append(table_name)
        connection.invalidate()

    if targets:
        if len(targets) > 20 or "arXiv_metadata" in targets:
            logger.error("Too many tables used in the database. Suspect this is not the intended test database.\n"
                         "Make sure you are not using any of production or even development database.")
            exit(1)
        statements = [ "SET FOREIGN_KEY_CHECKS = 0;"] + [f"TRUNCATE TABLE {table_name};" for table_name in targets] + ["SET FOREIGN_KEY_CHECKS = 1;"]
        # debug_sql = "SHOW PROCESSLIST;\nSELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;\n"
        sql = "\n".join(statements)
        cmd = my_sql_cmd
        if not use_ssl:
            cmd = my_sql_cmd + ["--ssl-mode=DISABLED"]
        cmd = cmd + [DB_NAME]
        mysql = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, encoding="utf-8")
        try:
            # logger.info(sql)
            out, err = mysql.communicate(sql, timeout=9999)
            if out:
                logger.info(out)
            if err and not err.startswith("[Warning] Using a password on the command line interface can be insecure"):
                logger.info(err)
        except Exception as exc:
            logger.error(f"BOO: {str(exc)}", exc_info=True)

    bootstrap_database(db_engine)
    return db_engine


def bootstrap_database(db_engine: Engine):
    test_data_dir = os.path.join(arxiv_base_dir(), "development", "test-data")
    bootstrap_arxiv_db(db_engine, test_data_dir=test_data_dir)

import shlex
import shutil
import sys, os
rooddir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(rooddir)

import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from arxiv.auth.user_claims import ArxivUserClaims, ArxivUserClaimsModel
from dotenv import dotenv_values, load_dotenv
from arxiv.config import Settings
from arxiv_bizlogic.database import Database, DatabaseSession

from arxiv_oauth2.biz.account_biz import AccountIdentifierModel

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest
import logging

from time import sleep

from fastapi.testclient import TestClient
from arxiv_oauth2.main import create_app
import os


MYSQL_DATA_DIR = AAA_TEST_DIR / "mysql-data"
MYSQL_SNAPSHOT_DIR = AAA_TEST_DIR / "mysql-data-snapshot"

DC_YAML = AAA_TEST_DIR.joinpath('docker-compose.yaml')


def _docker_rm_dir(host_path: Path) -> None:
    """Remove a directory using a Docker container running as root.

    This handles the case where the directory contents were created by a
    Docker container (e.g. MySQL) running as root and therefore cannot be
    removed by the host user with ``shutil.rmtree``.
    """
    uid, gid = get_non_root_uid_gid()
    abs_path = str(host_path.resolve())
    if Path(abs_path).parent.name != "tests":
        logging.error(f"Refusing to delete {abs_path}: parent directory is not 'tests'")
        return
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{abs_path}:/target",
            "alpine:latest",
            "sh", "-c", f"rm -rf /target/* /target/..?* /target/.[!.]* && chown {uid}:{gid} /target",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logging.warning(f"Docker cleanup of {host_path} failed: {result.stderr.strip()}")
        # Fall back to shutil if docker is unavailable
        shutil.rmtree(host_path, ignore_errors=True)


def pytest_sessionstart(session):
    """Clean up leftovers from previous test runs to ensure a fresh start."""
    logging.info("Cleaning up up docker-compose")
    if not DC_YAML.exists():
        raise FileNotFoundError(DC_YAML.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = AAA_TEST_DIR.as_posix()

    # Set UID/GID for docker-compose to run containers as current user
    docker_env = os.environ.copy()
    if "UID" not in docker_env or "GID" not in docker_env:
        uid, gid = get_non_root_uid_gid()
        docker_env["UID"] = str(uid)
        docker_env["GID"] = str(gid)

    args0 = ["docker", "compose", "--ansi=none", env_arg, "-f", DC_YAML.as_posix(), "down", "--remove-orphans"]
    try:
        logging.info(f"Stopping docker-compose: {shlex.join(args0)}")
        subprocess.run(args0, check=False, cwd=working_dir, env=docker_env)
    except Exception as e:
        logging.error(f"bad... {str(e)}")

    if MYSQL_SNAPSHOT_DIR.exists():
        logging.info(f"Removing stale snapshot: {MYSQL_SNAPSHOT_DIR}")
        _docker_rm_dir(MYSQL_SNAPSHOT_DIR)
        if MYSQL_SNAPSHOT_DIR.exists():
            MYSQL_SNAPSHOT_DIR.rmdir()
    if MYSQL_DATA_DIR.exists():
        logging.info(f"Removing stale mysql data: {MYSQL_DATA_DIR}")
        _docker_rm_dir(MYSQL_DATA_DIR)
        if MYSQL_DATA_DIR.exists():
            MYSQL_DATA_DIR.rmdir()



def ignore_socket_files(directory, files):
    """Ignore socket files when copying directory trees."""
    import stat
    ignored = []
    for f in files:
        path = Path(directory) / f
        try:
            if path.exists() and stat.S_ISSOCK(path.stat().st_mode):
                ignored.append(f)
        except (OSError, IOError):
            # If we can't stat the file, ignore it to be safe
            ignored.append(f)
    return ignored


def reset_database_from_snapshot(db_port: str, container_name: str = "aaat-arxiv-test-db") -> bool:
    """
    Reset the database to its initial state by restoring from snapshot.
    If snapshot doesn't exist, creates one from current data.
    If snapshot exists, restores the database from it.
    Snapshot is stored in mysql-data-snapshot directory on the local disk.
    """
    import shutil

    try:
        # Stop the container
        logging.info("Stopping container...")
        subprocess.run(
            ["docker", "stop", container_name],
            check=True,
            timeout=30
        )

        if not MYSQL_SNAPSHOT_DIR.exists():
            # Snapshot doesn't exist - create it from current data
            logging.info(f"Creating snapshot: copying {MYSQL_DATA_DIR} to {MYSQL_SNAPSHOT_DIR}...")
            shutil.copytree(MYSQL_DATA_DIR, MYSQL_SNAPSHOT_DIR, ignore=ignore_socket_files)
            logging.info("Snapshot created successfully")
        else:
            # Snapshot exists - restore from it
            logging.info("Restoring database from snapshot...")
            if MYSQL_DATA_DIR.exists():
                shutil.rmtree(MYSQL_DATA_DIR)
            shutil.copytree(MYSQL_SNAPSHOT_DIR, MYSQL_DATA_DIR, ignore=ignore_socket_files)
            logging.info("Database restored from snapshot")

        # Start the container (which will start MySQL)
        logging.info("Starting container...")
        subprocess.run(["docker", "start", container_name], check=True, timeout=30)

        # Wait for MySQL to be ready
        for _ in range(30):
            sleep(1)
            result = subprocess.run(
                ["docker", "exec", container_name, "mysqladmin",
                 "ping", "-h", "127.0.0.1", "-P", db_port, "--silent"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                logging.info("Database reset successfully")
                return True

        logging.error("Database failed to start after reset")
        return False

    except Exception as e:
        logging.error(f"Failed to reset database: {str(e)}")
        return False


def check_any_rows_in_table(schema: str, table_name: str, db_user: str, db_password: str, db_port: str = "3306", ssl: bool = True) -> bool:
    try:
        logging.info(f"Checking table {table_name} in schema {schema} on port {db_port}")
        result = subprocess.run(
            [
                "mysql",
                f"-u{db_user}",
                f"-p{db_password}",
                "-h", "127.0.0.1",
                "-P", db_port,
                "--default-auth=mysql_native_password",
                "-N",
                "-B",
                "-e", f"SELECT COUNT(*) FROM {table_name};",
                schema
            ],
            capture_output=True,
            text=True,
            check=False # Do not raise exception for non-zero exit codes
        )
        if result.returncode != 0:
            logging.error(f"MySQL command failed with exit code {result.returncode}")
            logging.error(f"Stdout: {result.stdout}")
            logging.error(f"Stderr: {result.stderr}")
            return False
        count = int(result.stdout.strip())
        logging.info(f"Table {table_name} has {count} rows.")
        return count > 0
    except subprocess.CalledProcessError as e:
        return False
    except ValueError:
        return False


@pytest.fixture(scope="module")
def test_env() -> Dict[str, Optional[str]]:
    if not AAA_TEST_DIR.joinpath(dotenv_filename).exists():
        raise FileNotFoundError(dotenv_filename)
    return dotenv_values(AAA_TEST_DIR.joinpath(dotenv_filename).as_posix())


def get_non_root_uid_gid() -> Tuple[int, int]:
    """Get the non-root UID and GID of the current user."""
    uid = os.getuid()
    gid = os.getgid()
    if uid == 0:
        return 1000, 1000
    return uid, gid


@pytest.fixture(scope="module")
def docker_compose(test_env):
    logging.info("Setting up docker-compose")
    if not DC_YAML.exists():
        raise FileNotFoundError(DC_YAML.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = AAA_TEST_DIR.as_posix()

    # Set UID/GID for docker-compose to run containers as current user
    docker_env = os.environ.copy()
    if "UID" not in docker_env or "GID" not in docker_env:
        uid, gid = get_non_root_uid_gid()
        docker_env["UID"] = str(uid)
        docker_env["GID"] = str(gid)

    args1 = ["docker", "compose", "--ansi=none", env_arg, "-f", DC_YAML.as_posix(), "up", "-d", ]
    try:
        logging.info(f"Starting docker-compose: {shlex.join(args1)}")
        result = subprocess.run(args1, capture_output=True, text=True, cwd=working_dir, env=docker_env)
        if result.stdout:
            logging.info(f"docker-compose stdout:\n{result.stdout}")
        if result.stderr:
            logging.info(f"docker-compose stderr:\n{result.stderr}")
        result.check_returncode()

        # Wait for keycloak-setup to complete (realm import, client setup, etc.)
        logging.info("Waiting for keycloak-setup to complete...")
        wait_args = ["docker", "compose", "--ansi=none", env_arg, "-f", DC_YAML.as_posix(),
                     "wait", "keycloak-setup"]
        wait_result = subprocess.run(wait_args, capture_output=True, text=True,
                                     cwd=working_dir, env=docker_env, timeout=300)
        if wait_result.stdout:
            logging.info(f"keycloak-setup wait stdout:\n{wait_result.stdout}")
        if wait_result.stderr:
            logging.info(f"keycloak-setup wait stderr:\n{wait_result.stderr}")
        if wait_result.returncode != 0:
            logging.error(f"keycloak-setup failed (exit {wait_result.returncode})")
            raise RuntimeError(f"keycloak-setup failed: {wait_result.stderr}")
        logging.info("keycloak-setup completed successfully.")

        # Loop until at least one row is present
        for _ in range(300):
            sleep(1)
            if check_any_rows_in_table(
                    "arXiv",
                    "tapir_users",
                    "arxiv", "arxiv_password",
                     db_port=test_env["ARXIV_DB_PORT"], ssl=False,):
                logging.info("Database is ready.")
                break
        else:
            assert False, "Failed to load "

        yield None
    except Exception as e:
        logging.error(f"bad... {str(e)}")

    finally:
        logging.info("Leaving the docker-compose as is...")


@pytest.fixture(scope="module")
def test_mta(test_env, docker_compose):
    return f"http://127.0.0.1:{test_env['MAIL_API_PORT']}"


@pytest.fixture(scope="module")
def aaa_client(test_env, docker_compose):
    """Start AAA App. Since it needs the database running, it needs the arxiv db up"""
    os.environ.update(test_env)
    app = create_app(TESTING=True)
    # aaa_app_port = test_env['ARXIV_OAUTH2_APP_PORT']
    aaa_url = test_env['AAA_URL']
    client = TestClient(app, base_url=aaa_url)

    for _ in range(100):
        response = client.get("/status/")
        if response.status_code == 200:
            logging.info("AAA status - OK")
            sleep(2)
            break
        sleep(2)
        logging.info("AAA status - WAITING")
        pass
    else:
        assert False, "The docker compose did not start?"
    yield client
    client.close()




@pytest.fixture(scope="module")
def aaa_api_headers(test_env):
    aaa_api_token = test_env['AAA_API_TOKEN']
    headers = {
        "Authorization": f"Bearer {aaa_api_token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def aaa_admin_user_headers(test_env):
    user_info = ArxivUserClaimsModel(
        sub = "1129053",
        exp = 253402300799,
        iat = 0,
        sid = "23276925",
        ts_id = 23276925,
        roles = ["Administrator", "CanLock", "Approved", "Public user"],
        email_verified = True,
        email = "<EMAIL>",
        first_name = "Cookie",
        last_name = "Monster",
        username = "cmonster",
    )
    claims = ArxivUserClaims(user_info)
    token = claims.encode_jwt_token(secret=test_env['JWT_SECRET'])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def aaa_user0001_headers(test_env, aaa_client, aaa_api_headers):
    response1 = aaa_client.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    first_user: AccountIdentifierModel = AccountIdentifierModel.model_validate(response1.json())

    user_claims = ArxivUserClaims(
        ArxivUserClaimsModel(
            acc="fake-access-token",
            sub = first_user.user_id,
            exp = 253402300799,
            iat = 1743465600,
            sid = "kc-session-1",
            roles = ["Approved", "Public user"],
            email_verified = True,
            email = first_user.email,
            first_name = "Test",
            last_name = "User",
            username = first_user.username,
            ts_id = 23276918,
        )
    )
    token = user_claims.encode_jwt_token(secret=test_env['JWT_SECRET'])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="function")
def reset_test_database(test_env, docker_compose):
    """
    Reset the database to its initial snapshot state before each test.
    Use this fixture when you need a clean database state for each test.
    """
    logging.info("Resetting database from snapshot...")
    success = reset_database_from_snapshot(db_port=test_env["ARXIV_DB_PORT"])
    if not success:
        pytest.fail("Failed to reset database from snapshot")
    yield None


@pytest.fixture(scope="module")
def database_session(test_env, docker_compose):
    """
    Set up the database connection for tests that need direct database access.
    This fixture configures the global Database instance and provides DatabaseSession.
    """

    db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}".format(
        "arxiv",
        "arxiv_password",
        "127.0.0.1",
        test_env["ARXIV_DB_PORT"],
        "arXiv"
    )

    settings = Settings(
        CLASSIC_DB_URI=db_uri,
        LATEXML_DB_URI=None
    )
    database = Database(settings)
    database.set_to_global()

    yield DatabaseSession

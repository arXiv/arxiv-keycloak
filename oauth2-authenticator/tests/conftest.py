#import sys, os
# rooddir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append(os.path.join(rooddir, "arxiv_oauth2"))

import subprocess
from pathlib import Path
from typing import Dict, Optional

from arxiv.auth.user_claims import ArxivUserClaims, ArxivUserClaimsModel
from dotenv import dotenv_values, load_dotenv

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
                "--ssl-mode=DISABLED",
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


@pytest.fixture(scope="module")
def docker_compose(test_env):
    logging.info("Setting up docker-compose")
    docker_compose_file = AAA_TEST_DIR.joinpath('docker-compose.yaml')
    if not docker_compose_file.exists():
        raise FileNotFoundError(docker_compose_file.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = AAA_TEST_DIR.as_posix()

    try:
        logging.info("Stopping docker-compose...")
        subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
        logging.info("Starting docker-compose...")
        subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "up", "-d"], check=True, cwd=working_dir)
        
        # Loop until at least one row is present
        for _ in range(100):
            sleep(1)
            if check_any_rows_in_table("arXiv", "tapir_users", "arxiv", "arxiv_password", db_port=test_env["ARXIV_DB_PORT"], ssl=False):
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
    app = create_app()
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
            ts_id = 1,
        )
    )
    token = user_claims.encode_jwt_token(secret=test_env['JWT_SECRET'])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def docker_compose_db_only(test_env):
    logging.info("Setting up database only")
    docker_compose_file = AAA_TEST_DIR.joinpath('docker-compose-db-only.yaml')
    if not docker_compose_file.exists():
        raise FileNotFoundError(docker_compose_file.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = AAA_TEST_DIR.as_posix()

    try:
        if os.environ.get("RECREATE_DOCKERS", "true") == "true":
            logging.info("Stopping docker-compose...")
            subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
            logging.info("Starting docker-compose...")
            subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "up", "-d"], check=True, cwd=working_dir)
            pass

        # Loop until at least one row is present
        for _ in range(100):
            sleep(1)
            if check_any_rows_in_table("arXiv", "tapir_users", "arxiv", "arxiv_password", db_port=test_env["ARXIV_DB_PORT"], ssl=False):
                break
        else:
            assert False, "Failed to load "

        yield None
    except Exception as e:
        logging.error(f"bad... {str(e)}")

    finally:
        logging.info("Leaving the docker-compose as is...")

    try:
        logging.info("Stopping docker-compose...")
        if os.environ.get("RECREATE_DOCKERS", "true") == "true":
            subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
    except Exception:
        pass


import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from dotenv import dotenv_values, load_dotenv

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest
import logging

from arxiv_bizlogic.bizmodels.user_model import VetoStatusEnum
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from datetime import datetime
from time import sleep

from arxiv_oauth2.biz.account_biz import CAREER_STATUS, AccountRegistrationModel, AccountInfoModel
from fastapi.testclient import TestClient
from arxiv_oauth2.main import create_app
import os

from test_mta_client.client import Client as MtaClient
from test_mta_client.api.default import get_emails_emails_get, maybe_click_link_emails_mail_id_verify_post
from test_mta_client.models import EmailRecord


def check_any_rows_in_table(schema: str, table_name: str, db_user: str, db_password: str, db_port: str = "3306", ssl: bool = True) -> bool:
    try:
        result = subprocess.run(
            [
                "mysql",
                f"-u{db_user}",
                f"-p{db_password}",
                "-h", "127.0.0.1",
                "-P", db_port,
                "--ssl-mode=ENABLED" if ssl else "--ssl-mode=DISABLED",
                "-N",
                "-B",
                "-e", f"SELECT COUNT(*) FROM {table_name};",
                schema
            ],
            capture_output=True,
            text=True,
            check=True
        )
        count = int(result.stdout.strip())
        return count > 0
    except subprocess.CalledProcessError as e:
        return False
    except ValueError:
        return False


@pytest.fixture(scope="session")
def test_env() -> Dict[str, Optional[str]]:
    if not AAA_TEST_DIR.joinpath(dotenv_filename).exists():
        raise FileNotFoundError(dotenv_filename)
    return dotenv_values(AAA_TEST_DIR.joinpath(dotenv_filename).as_posix())


@pytest.fixture(scope="session", autouse=True)
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
        subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def test_mta(test_env, docker_compose):
    return f"http://127.0.0.1:{test_env['MAIL_API_PORT']}"


@pytest.fixture(scope="session", autouse=True)
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

import subprocess
from pathlib import Path
from typing import Dict, Optional
from dotenv import dotenv_values, load_dotenv

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import httpx
import pytest
import logging

from arxiv_bizlogic.bizmodels.user_model import VetoStatusEnum
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from datetime import datetime
from time import sleep

from arxiv_oauth2.biz.account_biz import CAREER_STATUS, AccountRegistrationModel
from fastapi.testclient import TestClient
from arxiv_oauth2.main import create_app
import os


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

        yield None
    except Exception as e:
        logging.error(f"bad... {str(e)}")

    finally:
        logging.info("Leaving the docker-compose as is...")


@pytest.fixture(scope="session", autouse=True)
def aaa_client(test_env, docker_compose):
    """Start AAA App. Since it needs the database running, it needs the arxiv db up"""
    os.environ.update(test_env)
    app = create_app()
    # aaa_app_port = test_env['ARXIV_OAUTH2_APP_PORT']
    aaa_url = test_env['AAA_URL']
    client = TestClient(app, base_url=aaa_url)

    aaa_url = test_env['AAA_URL']

    for _ in range(10):
        try:
            response = client.get("/status/")
            if response.status_code == 200:
                break
        except httpx.ConnectError as _e:
            pass
        sleep(1)
        pass
    else:
        assert False
    yield client
    client.close()


@pytest.mark.asyncio
def test_register_account_success_with_token(docker_compose, test_env, aaa_client):
    # Wait for the backend to be up before making the request

    aaa_api_token = test_env['AAA_API_TOKEN']
    aaa_url = test_env['AAA_URL']

    registration_data = {
        "username": "jdoe",
        "email": "jdoe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecureP@ssword123",
        "token": "dummy-csrf-token",
        "captcha_value": "dummy-captcha",
        "keycloak_migration": False,
        "country": "US",
        "affiliation": "Example University",
        "career_status": CAREER_STATUS.PostDoc.value,
        "veto_status": VetoStatusEnum.ok.name,
        "joined_date": datetime_to_epoch(None, datetime.fromisoformat("2025-04-01T00:00:00Z")),
        "default_category": {
            "archive": "cs",
            "subject_class": "AI"
        },
        "groups": ["grp_cs", "grp_q-econ"],
    }

    data = AccountRegistrationModel.model_validate(registration_data)

    headers = {
        "Authorization": f"Bearer {aaa_api_token}",
        "Content-Type": "application/json"
    }

    response = aaa_client.post("/account/register/", json=data.model_dump(), headers=headers)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == "jdoe"
    assert data["email"] == "jdoe@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"

from pathlib import Path
from typing import List
from dotenv import load_dotenv

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_bizlogic.bizmodels.user_model import VetoStatusEnum
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from datetime import datetime
from time import sleep

from arxiv_oauth2.biz.account_biz import AccountRegistrationModel, CategoryIdModel, CAREER_STATUS, AccountInfoModel

from test_mta_client.client import Client as MtaClient
from test_mta_client.api.default import get_emails_emails_get
from test_mta_client.models import EmailRecord


@pytest.mark.asyncio
def test_register_account_success_with_token(docker_compose, test_env, aaa_client, test_mta, aaa_api_headers):
    # Wait for the backend to be up before making the request

    mta_client = MtaClient(base_url=test_mta)
    email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
    assert len(email_list) == 0

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

    # Make sure the registration data conforms
    input_data = AccountRegistrationModel.model_validate(registration_data)

    response1 = aaa_client.post("/account/register/", json=input_data.model_dump(), headers=aaa_api_headers)

    assert response1.status_code == 201
    user1 = AccountInfoModel.model_validate(response1.json())
    assert user1.username == "jdoe"
    assert user1.email == "jdoe@example.com"
    assert user1.email_verified == False
    assert user1.first_name == "John"
    assert user1.last_name == "Doe"

    for _ in range(10):
        email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
        if len(email_list) == 1:
            break
        sleep(1)
    else:
        assert False, "Email did not show up."

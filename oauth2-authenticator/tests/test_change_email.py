from pathlib import Path
from dotenv import load_dotenv
from typing import List
import time

from arxiv_oauth2.biz.account_biz import AccountIdentifierModel, AccountInfoModel

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.account import EmailUpdateModel

from test_mta_client.client import Client as MtaClient
from test_mta_client.api.default import get_emails_emails_get
from test_mta_client.models import EmailRecord

@pytest.mark.asyncio
def test_change_email(docker_compose, test_env, aaa_client, test_mta, aaa_api_headers):
    # When you try to change email when the user is not in KC yet, this triggers migration
    mta_client = MtaClient(base_url=test_mta)
    email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
    initial_email_count = len(email_list)

    response1 = aaa_client.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    response2 = aaa_client.get(f"/account/profile/{ident.user_id}", headers=aaa_api_headers)
    profile2 = AccountInfoModel.model_validate(response2.json())

    assert profile2.email_verified == True

    email_data = EmailUpdateModel(
        user_id=ident.user_id,
        email = profile2.email,
        new_email="notemail"
    )
    response3 = aaa_client.put("/account/email/", json=email_data.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 400

    email_data = EmailUpdateModel(
        user_id=ident.user_id,
        email = profile2.email,
        new_email="foo@example.com"
    )
    response4 = aaa_client.put("/account/email/", json=email_data.model_dump(), headers=aaa_api_headers)
    assert response4.status_code == 200

    # Change email request
    for _ in range(10):
        email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
        if len(email_list) > initial_email_count:
            initial_email_count = len(email_list)
            break
        time.sleep(1)
    else:
        assert False, "Email did not show up."

    response5 = aaa_client.get(f"/account/profile/{ident.user_id}", headers=aaa_api_headers)
    profile5 = AccountInfoModel.model_validate(response5.json())

    assert profile5.email_verified == False

    # 2nd try exercises the case where the account exists on KC

    email_data = EmailUpdateModel(
        user_id=ident.user_id,
        email = profile5.email,
        new_email="bar@example.com"
    )
    response6 = aaa_client.put("/account/email/", json=email_data.model_dump(), headers=aaa_api_headers)
    assert response6.status_code == 200

    # should the 2nd email
    for _ in range(10):
        email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
        if len(email_list) > initial_email_count:
            initial_email_count = len(email_list)
            break
        time.sleep(1)
    else:
        assert False, "Email did not show up."

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
def test_change_email(docker_compose, test_env, aaa_client, test_mta, aaa_api_headers, aaa_user0001_headers):
    # When you try to change email when the user is not in KC yet, this triggers migration
    mta_client = MtaClient(base_url=test_mta)
    email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
    initial_email_count = len(email_list)

    response1 = aaa_client.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    # You can get your profile with API
    response2 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    assert response2.status_code == 200
    profile2 = AccountInfoModel.model_validate(response2.json())

    assert profile2.email_verified == True

    # Request a email change - with api token - not supported
    email_data = EmailUpdateModel(
        email = profile2.email,
        new_email="notemail"
    )
    response3 = aaa_client.put(f"/account/{ident.user_id}/email", json=email_data.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 401, "API token does not work for changing email"

    # bad email address
    response3_1 = aaa_client.put(f"/account/{ident.user_id}/email", json=email_data.model_dump(), headers=aaa_user0001_headers)
    assert response3_1.status_code == 400, "email address validation failed."

    # This email already exists - returns conflict error
    email_data = EmailUpdateModel(
        email = profile2.email,
        new_email="foo@example.com"
    )
    response4_0 = aaa_client.put(f"/account/{ident.user_id}/email", json=email_data.model_dump(), headers=aaa_user0001_headers)
    assert response4_0.status_code == 409

    # good email
    new_email = "foo7000@example.com"
    email_data = EmailUpdateModel(
        email = profile2.email,
        new_email=new_email
    )
    response4_1 = aaa_client.put(f"/account/{ident.user_id}/email", json=email_data.model_dump(), headers=aaa_user0001_headers)
    assert response4_1.status_code == 200

    # Change email request - did it issue a verify email?
    for _ in range(10):
        email_list: List[EmailRecord] = get_emails_emails_get.sync(client=mta_client)
        if len(email_list) > initial_email_count:
            initial_email_count = len(email_list)
            break
        time.sleep(1)
    else:
        assert False, "Email did not show up."

    # email hasn't been verified
    response5 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_user0001_headers)
    profile5 = AccountInfoModel.model_validate(response5.json())
    assert response5.status_code == 200
    # When you request the email change, tapir's email stays as is. KC sends the email change verify to the user,
    # and when the email verified, the audit event updates the user's email.
    # on Keycloak, it knows the email change is requested, and marked as unverified but for tapir, this is correct.
    # This way, the user can still log in using old email until the new email is verified.
    assert profile5.email_verified == True
    assert profile5.email != new_email

    #
    # email change mock audit event
    audit = {
        "id": "3ebfbf2e-3847-4273-a083-25c9592a4d02",
        "time": 1755118023735,
        "type": "VERIFY_EMAIL",
        "realmName": "arxiv",
        "clientId": "arxiv-user",
        "userId": str(ident.user_id),
        "ipAddress": "127.0.0.1",
        "details": {
            "auth_method": "openid-connect",
            "token_id": "d413779e-8dc7-4e52-a65a-46682d6f2857",
            "action": "verify-email",
            "response_type": "code",
            "redirect_uri": "http://localhost.arxiv.org:5100/aaa/callback",
            "remember_me": "true",
            "code_id": "158aff32-51ba-4e01-86f5-dfdaf1044c5c",
            "email": new_email,
            "response_mode": "query",
            "username": ident.username
        }
    }

    response7 = aaa_client.post("/keycloak/audit/", json=audit, headers=aaa_api_headers)
    assert response7.status_code == 200

    # email is verified, changed
    response8 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_user0001_headers)
    assert response8.status_code == 200
    profile8 = AccountInfoModel.model_validate(response8.json())
    assert profile8.email_verified == True
    assert profile8.email == new_email


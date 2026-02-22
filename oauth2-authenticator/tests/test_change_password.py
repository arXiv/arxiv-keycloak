from pathlib import Path

from arxiv_bizlogic.fastapi_helpers import sha256_base64_encode
from dotenv import load_dotenv

from arxiv_oauth2.biz.account_biz import AccountIdentifierModel
from conftest import kc_login_and_set_cookie

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.account import PasswordUpdateModel


@pytest.mark.asyncio
def test_change_password(docker_compose, test_env, aaa_client, aaa_api_headers, aaa_admin_user_headers, aaa_user0001_headers):

    response1 = aaa_client.get("/account/identifier?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    change_password_data = PasswordUpdateModel(
        old_password="wrong-password",
        new_password="P"
    )
    # You cannot change the password with API secret
    response2_0 = aaa_client.put(f"/account/{ident.user_id}/password", json=change_password_data.model_dump(), headers=aaa_api_headers)
    assert response2_0.status_code == 401

    # password is way too short - bad request
    response2_1 = aaa_client.put(f"/account/{ident.user_id}/password", json=change_password_data.model_dump(), headers=aaa_user0001_headers)
    assert response2_1.status_code == 400

    # old password is incorrect
    change_password_data = PasswordUpdateModel(
        old_password="wrong-password",
        new_password="<PASS_WORD>"
    )
    response3 = aaa_client.put(f"/account/{ident.user_id}/password", json=change_password_data.model_dump(), headers=aaa_user0001_headers)
    assert response3.status_code == 401

    # should be success - by admin
    temp_old_password = sha256_base64_encode("changeme")
    change_password_data = PasswordUpdateModel(
        old_password=temp_old_password,
        new_password="change_m3!"
    )
    response4 = aaa_client.put(f"/account/{ident.user_id}/password", json=change_password_data.model_dump(), headers=aaa_admin_user_headers)
    assert response4.status_code == 200

    # Mark user's email verified so it can log in to Keycloak
    email_verified_data = {"email_verified": True, "user_id": str(ident.user_id)}
    response5 = aaa_client.put(f"/account/{ident.user_id}/email/verified", json=email_verified_data, headers=aaa_admin_user_headers)
    assert response5.status_code == 200

    # Log in to Keycloak as user0001 with the new password to get an access token cookie
    client_secret = test_env['ARXIV_USER_SECRET']
    assert kc_login_and_set_cookie(aaa_client, "user0001", "change_m3!", client_secret), \
        "Failed to get Keycloak access token for user0001"

    # should be success
    change_password_data = PasswordUpdateModel(
        old_password="change_m3!",
        new_password="<P4SS_WORD!>"
    )
    response6 = aaa_client.put(f"/account/{ident.user_id}/password", json=change_password_data.model_dump(), headers=aaa_user0001_headers)
    assert response6.status_code == 200


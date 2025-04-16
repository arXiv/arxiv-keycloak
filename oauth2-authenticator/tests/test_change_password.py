from pathlib import Path
from dotenv import load_dotenv

from arxiv_oauth2.biz.account_biz import AccountIdentifierModel

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.account import PasswordUpdateModel


@pytest.mark.asyncio
def test_change_password(docker_compose, test_env, aaa_client, aaa_api_headers):

    response1 = aaa_client.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    change_password_data = PasswordUpdateModel(
        user_id=ident.user_id,
        old_password="wrong-password",
        new_password="<PASSWORD>"
    )
    response3 = aaa_client.put("/account/password/", json=change_password_data.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 200

    change_password_data = PasswordUpdateModel(
        user_id=ident.user_id,
        old_password="changeme",
        new_password="<PASSWORD>"
    )
    response4 = aaa_client.put("/account/password/", json=change_password_data.model_dump(), headers=aaa_api_headers)
    assert response4.status_code == 200


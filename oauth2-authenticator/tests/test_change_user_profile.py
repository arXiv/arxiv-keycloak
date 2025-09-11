from pathlib import Path
from dotenv import load_dotenv

AAA_TEST_DIR = Path(__file__).parent
ARXIV_KEYCLOAK_DIR = AAA_TEST_DIR.parent.parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.biz.account_biz import AccountInfoModel, AccountIdentifierModel


@pytest.mark.asyncio
def test_change_user_profile(docker_compose, test_env, aaa_client, aaa_api_headers):

    response1 = aaa_client.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    response2 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    profile2 = AccountInfoModel.model_validate(response2.json())

    profile2.affiliation = "Mandalore"
    response3 = aaa_client.put(f"/account/{ident.user_id}/profile", json=profile2.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 200

    response3 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    profile3 = AccountInfoModel.model_validate(response3.json())

    assert profile3.affiliation == "Mandalore"

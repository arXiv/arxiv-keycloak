from pathlib import Path
from dotenv import load_dotenv

AAA_TEST_DIR = Path(__file__).parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.biz.account_biz import AccountInfoModel, AccountIdentifierModel
from arxiv.db.models import TapirAdminAudit
from arxiv_bizlogic.database import Database

@pytest.mark.asyncio
def test_change_user_profile(test_env, aaa_client_db_only, aaa_api_headers, aaa_admin_user, reset_test_database):

    # Test non-audit
    response1 = aaa_client_db_only.get("/account/identifier/?username=user0001", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    response2 = aaa_client_db_only.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    profile2 = AccountInfoModel.model_validate(response2.json())

    profile2.affiliation = "Mandalore"
    response3 = aaa_client_db_only.put(f"/account/{ident.user_id}/profile", json=profile2.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 200

    response3 = aaa_client_db_only.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    profile3 = AccountInfoModel.model_validate(response3.json())

    assert profile3.affiliation == "Mandalore"

    db = Database.get_from_global()
    session = next(db.get_session())
    try:
        query = session.query(TapirAdminAudit.entry_id).order_by(TapirAdminAudit.entry_id.desc()).limit(1)
        audit_before = query.scalar()
    finally:
        session.close()

    profile2.first_name = "Test"
    profile2.last_name = "User"
    response4 = aaa_client_db_only.put(f"/account/{ident.user_id}/profile", json=profile2.model_dump(), headers=aaa_admin_user)
    assert response4.status_code == 200

    session = next(db.get_session())
    try:
        query = session.query(TapirAdminAudit).order_by(TapirAdminAudit.entry_id.desc()).limit(1)
        audit_after: TapirAdminAudit | None = query.one_or_none()
    finally:
        session.close()

    # Verify that an audit record was created for the name change
    assert audit_after is not None
    if audit_before is not None:
        assert audit_after.entry_id > audit_before
    assert str(audit_after.action) == "change-demographic"
    assert str(audit_after.data) == '{"before": {"first_name": "Garret", "last_name": "Zieme", "suffix_name": ""}, "after": {"first_name": "Test", "last_name": "User", "suffix_name": ""}}'
    assert str(audit_after.comment) == ""

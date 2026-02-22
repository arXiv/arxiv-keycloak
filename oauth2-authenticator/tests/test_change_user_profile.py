from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import LargeBinary, cast

AAA_TEST_DIR = Path(__file__).parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=AAA_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest

from arxiv_oauth2.biz.account_biz import AccountInfoModel, AccountIdentifierModel
from arxiv.db.models import TapirAdminAudit
from arxiv_bizlogic.database import Database

@pytest.mark.asyncio
def test_change_user_profile(test_env, aaa_client, aaa_api_headers, aaa_admin_user_headers):

    # Test non-audit
    response1 = aaa_client.get("/account/identifier/?username=user0002", headers=aaa_api_headers)
    ident = AccountIdentifierModel.model_validate(response1.json())

    response2 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
    profile2 = AccountInfoModel.model_validate(response2.json())

    profile2.affiliation = "Mandalore"
    response3 = aaa_client.put(f"/account/{ident.user_id}/profile", json=profile2.model_dump(), headers=aaa_api_headers)
    assert response3.status_code == 200

    response3 = aaa_client.get(f"/account/{ident.user_id}/profile", headers=aaa_api_headers)
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
    response4 = aaa_client.put(f"/account/{ident.user_id}/profile", json=profile2.model_dump(), headers=aaa_admin_user_headers)
    assert response4.status_code == 200

    session = next(db.get_session())
    try:
        query = session.query(
            TapirAdminAudit.entry_id,
            TapirAdminAudit.log_date,
            TapirAdminAudit.session_id,
            TapirAdminAudit.ip_addr,
            TapirAdminAudit.remote_host,
            TapirAdminAudit.admin_user,
            TapirAdminAudit.affected_user,
            TapirAdminAudit.tracking_cookie,
            TapirAdminAudit.action,
            cast(TapirAdminAudit.data, LargeBinary).label("data"),
            cast(TapirAdminAudit.comment, LargeBinary).label("comment")
        ).order_by(TapirAdminAudit.entry_id.desc()).limit(1)
        audit_after: Any | None = query.one_or_none()  # type: ignore
    finally:
        session.close()

    # Verify that an audit record was created for the name change
    assert audit_after is not None
    if audit_before is not None:
        assert audit_after.entry_id > audit_before
    assert str(audit_after.action) == "change-demographic"
    # The data is json.dumps() and it encodes the dict in ASCII safe.
    assert audit_after.data.decode('utf-8')) == r'{"before": {"first_name": "George", "last_name": "Fr\u00e9d\u00e9rique", "suffix_name": ""}, "after": {"first_name": "Test", "last_name": "User", "suffix_name": ""}}'
    assert str(audit_after.comment.decode('utf-8')) == r""

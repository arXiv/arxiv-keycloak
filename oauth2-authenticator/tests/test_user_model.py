from arxiv.db.models import TapirUser, Demographic

from arxiv_oauth2.biz.account_biz import AccountRegistrationModel, CategoryIdModel, CAREER_STATUS
from arxiv_bizlogic.bizmodels.user_model import UserModel, _tapir_user_utf8_fields_, _demographic_user_utf8_fields_


def test_user_model():
    registration_data = AccountRegistrationModel(
        username="arxiv-test-user#1",
        first_name=u"めい",
        last_name=u"せい",
        suffix_name="無視",
        email="foo@例.com",
        password="changeme",
        affiliation=u"アーカイブ",
        url="https://例.co.jp",
        country="JP",
        default_category=CategoryIdModel(archive="cs", subject_class="AI"),
        groups=[],
        oidc_id=None,
        origin_ip=None,
        origin_host=None,
        token="foo",
        captcha_value="bar",
        career_status=CAREER_STATUS.Other,
        joined_date=0,
        tracking_cookie="test-tracking-cookie",
    )
    data = registration_data.to_user_model_data()
    um = UserModel.to_model(data)
    assert um is not None

    from_fields = set(um.__class__.model_fields.keys())
    to_fields = set([column.key for column in TapirUser.__mapper__.column_attrs])
    data = {}
    for field in to_fields:
        from_field = "id" if field == "user_id" else field
        if from_field in from_fields:
            data[field] = getattr(um, from_field)

    unfilled_fields = to_fields - set(data.keys())
    assert len(unfilled_fields) == 0

    for field in _tapir_user_utf8_fields_:
        data[field] = data[field].encode("utf-8").decode("iso-8859-1")

    db_user = TapirUser(**data)
    assert db_user is not None

    to_fields = set([column.key for column in Demographic.__mapper__.column_attrs])

    demographic = {}
    for field in to_fields:
        from_field = "id" if field == "user_id" else field
        if from_field in from_fields:
            demographic[field] = getattr(um, from_field)
    demographic["user_id"] = db_user.user_id
    demographic["dirty"] = 0

    unfilled_fields = to_fields - set(demographic.keys())
    assert len(unfilled_fields) == 0

    for field in _demographic_user_utf8_fields_:
        demographic[field] = demographic[field].encode("utf-8").decode("iso-8859-1")

    db_demographic = Demographic(**demographic)
    assert db_demographic is not None


def test_fields():
    assert "username" in AccountRegistrationModel.model_fields

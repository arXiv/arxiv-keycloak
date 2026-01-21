import pytest
from datetime import datetime

from arxiv.db.models import TapirUser
from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from arxiv_oauth2.biz.account_biz import (
    register_tapir_account,
    AccountRegistrationModel,
    get_account_info,
    CategoryIdModel,
    CAREER_STATUS,
    CategoryGroup,
    AccountInfoModel,
    update_tapir_account,
)


class TestRegisterUser:

    def test_register_user_0(self, database_session):
        """Test registering a new user with all fields populated."""
        registration = AccountRegistrationModel(
            username="test-user-0",
            first_name="First",
            last_name="Last",
            suffix_name="Non",
            email="foo@example.com",
            password="changeme",
            affiliation="Example",
            url="https://example.com",
            country="US",
            default_category=CategoryIdModel(archive="cs", subject_class="AI"),
            groups=[CategoryGroup.ECON, CategoryGroup.PHYSICS, CategoryGroup.MATH, CategoryGroup.CS],
            joined_date=datetime_to_epoch(None, datetime.now()),
            oidc_id="fake-oidc-id",
            origin_ip="4.4.4.4",
            origin_host="dns.example.com",
            token="foo",
            captcha_value="bar",
            career_status=CAREER_STATUS.Other,
            tracking_cookie="test-tracking-cookie",
        )

        user_id = None
        with database_session() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        assert user_id is not None

        with database_session() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            assert user is not None

            info = get_account_info(session, user_id)
            assert registration.username == info.username
            assert registration.first_name == info.first_name
            assert registration.last_name == info.last_name
            assert registration.suffix_name == info.suffix_name
            assert registration.email == info.email
            assert registration.affiliation == info.affiliation
            assert registration.url == info.url
            assert registration.country == info.country
            assert registration.default_category == info.default_category
            assert set(registration.groups) == set(info.groups)

    @pytest.mark.xfail(reason="Insert Japanese letters violates Latin-1 code points and causes sqlalchemy.exc.OperationalError")
    def test_register_user_1(self, database_session):
        """Insert Japanese letters violates Latin-1 code points and causes sqlalchemy.exc.OperationalError"""
        registration = AccountRegistrationModel(
            username="atest-user#1",
            first_name="めい",
            last_name="せい",
            suffix_name="無視",
            email="foo@例.com",
            password="changeme",
            affiliation="アーカイブ",
            url="https://例.co.jp",
            country="JP",
            default_category=CategoryIdModel(archive="cs", subject_class="AI"),
            groups=[],
            joined_date=datetime_to_epoch(None, datetime.now()),
            oidc_id=None,
            origin_ip=None,
            origin_host=None,
            token="foo",
            captcha_value="bar",
            career_status=CAREER_STATUS.Other,
            tracking_cookie="test-tracking-cookie",
        )

        user_id = None
        with database_session() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        assert user_id is not None

        with database_session() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            assert user is not None

            info = get_account_info(session, user_id)
            assert registration.first_name == info.first_name
            assert registration.last_name == info.last_name
            assert registration.email == info.email
            assert registration.affiliation == info.affiliation
            assert registration.url == info.url

    def test_update_user_0(self, database_session):
        """Test updating a user's information."""
        username = "test-user-2"

        registration = AccountRegistrationModel(
            username=username,
            first_name="Second",
            last_name="Last",
            suffix_name="Jr",
            email="bar@example.com",
            password="changeme",
            affiliation="Example",
            url="https://example.com",
            country="US",
            default_category=CategoryIdModel(archive="cs", subject_class="AI"),
            groups=[CategoryGroup.ECON, CategoryGroup.PHYSICS, CategoryGroup.MATH, CategoryGroup.CS],
            joined_date=datetime_to_epoch(None, datetime.now()),
            oidc_id="fake-oidc-id",
            origin_ip="4.4.4.4",
            origin_host="dns.example.com",
            token="foo",
            captcha_value="bar",
            career_status=CAREER_STATUS.Other,
            tracking_cookie="test-tracking-cookie",
        )

        user_id = None
        with database_session() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        with database_session() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            assert user is not None

            info = get_account_info(session, user_id)
            assert registration.username == info.username
            assert registration.first_name == info.first_name
            assert registration.last_name == info.last_name
            assert registration.suffix_name == info.suffix_name
            assert registration.email == info.email
            assert registration.affiliation == info.affiliation
            assert registration.url == info.url
            assert registration.country == info.country
            assert registration.default_category == info.default_category
            assert set(registration.groups) == set(info.groups)

        with database_session() as session:
            um0 = UserModel.one_user_from_username(session, username)

            new_info = AccountInfoModel(
                id=str(user_id),
                username=username,
                first_name="FirstName",
                last_name="LastName",
                email_verified=True
            )
            update_tapir_account(session, new_info)

        with database_session() as session:
            um1 = UserModel.one_user_from_username(session, username)
            assert um1 is not None

            from_dict = um0.model_dump()
            to_dict = um1.model_dump()

            diff_dict = from_dict.copy()
            for key, value in to_dict.items():
                if from_dict.get(key) == value:
                    del diff_dict[key]
            assert {'first_name': 'Second', 'last_name': 'Last'} == diff_dict
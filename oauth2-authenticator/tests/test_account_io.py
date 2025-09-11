import os
import subprocess
import time
import unittest
from datetime import datetime
from pathlib import Path
# from typing import List

from arxiv.db.models import TapirUser, TapirNickname
from arxiv_bizlogic.bizmodels.user_model import UserModel

#from pygments.lexer import default

from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from arxiv_oauth2.biz.account_biz import register_tapir_account, AccountRegistrationModel, get_account_info, \
    CategoryIdModel, CAREER_STATUS, CategoryGroup, AccountInfoModel, update_tapir_account

AAA_TEST_DIR = Path(__file__).parent
AAA_DIR = AAA_TEST_DIR.parent
PROJECT_ROOT = AAA_DIR.parent
PROJECT_TEST_DIR = PROJECT_ROOT.joinpath("tests")

HOST = "127.0.0.1"
DB_PORT = 21701
DB_USER = "arxiv"
DB_PASSWORD = "arxiv_password"
MAX_RETRIES = 10
RETRY_DELAY = 2
DOCKER_COMPOSE_ARGS = [
    "docker", "compose", "-f",
    str(PROJECT_ROOT.joinpath("tests", "docker-compose-for-test.yaml").as_posix())
]
DOCKER_ENV = os.environ.copy()
DOCKER_ENV["ARXIV_DB_PORT"] = str(DB_PORT)


class TestRegisterUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # docker compose -f ./docker-compose-for-test.yaml --env-file=./test-env  up
        subprocess.run(DOCKER_COMPOSE_ARGS + ["down"], env=DOCKER_ENV, cwd=PROJECT_TEST_DIR.as_posix())
        subprocess.run(DOCKER_COMPOSE_ARGS + ["up", "-d"], env=DOCKER_ENV, cwd=PROJECT_TEST_DIR.as_posix())

        db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}?ssl=false&ssl_mode=DISABLED".format(DB_USER, DB_PASSWORD, HOST, DB_PORT, "arXiv")
        from arxiv.config import Settings
        settings = Settings(
            CLASSIC_DB_URI = db_uri,
            LATEXML_DB_URI = None
        )
        from arxiv_bizlogic.database import Database, DatabaseSession
        database = Database(settings)
        database.set_to_global()

        for _ in range(10):
            try:
                with DatabaseSession() as session:
                    users = session.query(TapirUser).all()
                    if len(users) > 0:
                        break
            except Exception as exc:
                print(exc)
                time.sleep(5)
                continue


    def test_register_user_0(self):
        from arxiv_bizlogic.database import DatabaseSession

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
        with DatabaseSession() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        self.assertIsNotNone(user_id)

        with DatabaseSession() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            self.assertIsNotNone(user)

            info = get_account_info(session, user_id)
            self.assertEqual(registration.username, info.username)
            self.assertEqual(registration.first_name, info.first_name)
            self.assertEqual(registration.last_name, info.last_name)
            self.assertEqual(registration.suffix_name, info.suffix_name)
            self.assertEqual(registration.email, info.email)
            self.assertEqual(registration.affiliation, info.affiliation )
            self.assertEqual(registration.url, info.url)
            self.assertEqual(registration.country, info.country)
            self.assertEqual(registration.default_category, info.default_category)
            self.assertEqual(set(registration.groups), set(info.groups))


    @unittest.expectedFailure
    def test_register_user_1(self):
        """Insert Japanese letters violates Latin-1 code points and causes sqlalckemy.exc.OpesationalError"""
        from arxiv_bizlogic.database import DatabaseSession

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
        with DatabaseSession() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        self.assertIsNotNone(user_id)

        with DatabaseSession() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            self.assertIsNotNone(user)

            info = get_account_info(session, user_id)
            self.assertEqual(registration.first_name, info.first_name)
            self.assertEqual(registration.last_name, info.last_name)
            self.assertEqual(registration.email, info.email)
            self.assertEqual(registration.affiliation, info.affiliation )
            self.assertEqual(registration.url, info.url)


    def test_update_user_0(self):
        from arxiv_bizlogic.database import DatabaseSession
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
        with DatabaseSession() as session:
            result = register_tapir_account(session, registration)
            if isinstance(result, TapirUser):
                user_id = result.user_id

        with DatabaseSession() as session:
            user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            self.assertIsNotNone(user)

            info = get_account_info(session, user_id)
            self.assertEqual(registration.username, info.username)
            self.assertEqual(registration.first_name, info.first_name)
            self.assertEqual(registration.last_name, info.last_name)
            self.assertEqual(registration.suffix_name, info.suffix_name)
            self.assertEqual(registration.email, info.email)
            self.assertEqual(registration.affiliation, info.affiliation )
            self.assertEqual(registration.url, info.url)
            self.assertEqual(registration.country, info.country)
            self.assertEqual(registration.default_category, info.default_category)
            self.assertEqual(set(registration.groups), set(info.groups))


        with DatabaseSession() as session:
            um0 = UserModel.one_user_from_username(session, username)

            new_info = AccountInfoModel(
                id = str(user_id),
                username = username,
                first_name = "FirstName",
                last_name = "LastName",
                email_verified = True
            )
            update_tapir_account(session, new_info)

        with DatabaseSession() as session:
            um1 = UserModel.one_user_from_username(session, username)
            self.assertIsNotNone(um1)

            from_dict = um0.model_dump()
            to_dict = um1.model_dump()

            diff_dict = from_dict.copy()
            for key, value in to_dict.items():
                if from_dict.get(key) == value:
                    del diff_dict[key]
            self.assertEqual({'first_name': 'Second', 'last_name': 'Last'}, diff_dict)


if __name__ == '__main__':
    unittest.main()

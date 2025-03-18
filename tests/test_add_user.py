import os
from typing import Optional

from MySQLdb._mysql import IntegrityError
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from arxiv.util.dict_io import from_file_to_dict
from arxiv.auth.legacy import accounts, authenticate, exceptions
from arxiv.auth import domain
from arxiv.taxonomy.definitions import GROUPS, CATEGORIES
from arxiv.db import Session
from arxiv.db.models import TapirNickname

from . import ROOT_DIR

def get_dom_user(filename: str) -> domain.User:

    test_data = from_file_to_dict(os.path.join(ROOT_DIR, "tests", "small-data", filename))
    user = test_data['tapir_users'][0]
    user_email = user['email']
    nick = test_data['tapir_nicknames'][0]
    full_name: domain.UserFullName = domain.UserFullName(
        forename = user['first_name'], surname = user['last_name'], suffix=user.get('suffix', '')
    )
    group_keys = list(GROUPS.keys())
    profile: domain.UserProfile = domain.UserProfile(
        affiliation = "Sesami Street",
        country = "us",
        rank = domain.OTHER[0],
        submission_groups = [group_keys[3], group_keys[4]],
        default_category = CATEGORIES['cs.AI'],
        homepage_url = 'localhost',
        remember_me = True
    )

    dom_user = domain.User(
        username=nick['nickname'],
        email=user_email,
        name=full_name,
        profile=profile,
    )
    return dom_user

def get_user_id_from_login_name(session, username: str) -> Optional[int]:
    data: TapirNickname = Session.query(TapirNickname).filter(TapirNickname.nickname == username).one_or_none()
    return None if data is None else data.user_id


def test_add_user(localenv: dict, configured_db: Engine):
    password = "changeme"

    ernie = get_dom_user("ernie.yaml")
    bert = get_dom_user("bert.yaml")
    big_bird = get_dom_user("big-bird.yaml")

    for character in [ernie, bert, big_bird]:
        with Session() as session:
            user_id = get_user_id_from_login_name(session, character.username)
            if user_id:
                character.user_id = user_id
                accounts.update(character)
            else:
                accounts.register(character, password, '10.11.12.13', 'localhost')
            session.commit()

        with Session() as session:
            dom_user, auth  = authenticate.authenticate(character.email, password)
            assert dom_user is not None
            assert dom_user.username == character.username

import os
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from arxiv.util.dict_io import from_file_to_dict
from arxiv.auth.legacy import accounts, authenticate
from arxiv.auth import domain
from arxiv.taxonomy.definitions import GROUPS, CATEGORIES
from arxiv.db import Session

from . import ROOT_DIR

def get_dom_user(filename: str) -> domain.User:

    test_data = from_file_to_dict(os.path.join(ROOT_DIR, "tests", "data", filename))
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


def test_add_user(localenv: dict, configured_db: Engine):
    password = "changeme"

    ernie = get_dom_user("ernie.yaml")
    bert = get_dom_user("bert.yaml")
    big_bird = get_dom_user("big-bird.yaml")

    for character in [ernie, bert, big_bird]:
        with Session() as session:
            accounts.register(character, password, '10.11.12.13', 'localhost')
            session.commit()

        with Session() as session:
            dom_user, auth  = authenticate.authenticate(character.email, password)
            assert dom_user is not None
            assert dom_user.username == character.username

import argparse
import json
import os

from arxiv.auth.legacy.passwords import hash_password
from sqlalchemy import func, Engine, Table, update, text

from load_test_data import instantiate_db_engine
from arxiv.db.models import TapirUser, TapirUsersPassword, TapirNickname
from arxiv.db import Base, LaTeXMLBase
from sqlalchemy.orm import Session

from remap_users import get_mysql_table_charset, make_map_data
from thirdparty.random_name_generator import random_names

EMAIL_COLUMNS = [
    ("arXiv_admin_metadata","submitter_email"),
    ("arXiv_bib_feeds","email_errors"),
    ("tapir_email_change_tokens", "old_email"),
    ("tapir_email_change_tokens", "new_email"),
    ("tapir_email_log", "email"),
    ("tapir_users", "email"),
]

USERNAME_COLUMNS = [
    ("arXiv_admin_log","username",),
    ("arXiv_reject_session_usernames","username"),
]

NAME_COLUMNS = [
    ("arXiv_admin_metadata", "submitter_name"),
    ("arXiv_dblp_authors", "name"),
    ("arXiv_state", "name"),
    # Tapir's original names are smashed
    # ("tapir_users", "first_name"),
    # ("tapir_users", "last_name"),
    # ("tapir_users", "suffix_name"),
]

def random_3k():
    result = []
    index = 0
    for filename in ["random-1.json", "random-2.json", "random-3.json"]:
        with open(os.path.join("../tests/data/", filename)) as data_fd:
            randoms = json.load(data_fd)
            for row in randoms:
                index = index + 1
                row['id'] = index
            result.extend(randoms)
    return result


def main() -> None:
    db_engine, tables = instantiate_db_engine()
    email_map, name_map, username_map = make_map_data()

    randoms = random_3k()
    emails = set([person['email'].lower() for person in randoms])
    usernames = set([person['email'].lower().split('@')[0] for person in randoms])

    first_names = random_names.DataSource(random_names.FirstNames)
    last_names = random_names.DataSource(random_names.LastNames)

    names = [first_names.pick() + " " + last_names.pick() for _ in range(230000)]

    new_email_map = collect_data(db_engine, email_map, EMAIL_COLUMNS, list(emails))
    new_username_map = collect_data(db_engine, username_map, USERNAME_COLUMNS, list(usernames))
    new_name_map = collect_data(db_engine, name_map, NAME_COLUMNS, names)



def collect_data(db_engine, map_dict, cleansing_targets, supplements) -> dict:
    Base.metadata.reflect(db_engine)
    result = map_dict.copy()
    index = 0

    with Session(db_engine) as session:
        for table_name, column_name in cleansing_targets:
            table_class: Table = Base.metadata.tables[table_name]
            table_charset = get_mysql_table_charset(db_engine, table_name)
            if table_charset:
                is_utf8_table = table_charset.find('utf8') != -1
            #column_index = table_class.columns.keys().index(column_name)

            primary_keys = [col.name for col in table_class.primary_key.columns]
            if not primary_keys:
                raise ValueError(f"Table {table_name} has no primary key, cannot update reliably.")
            rows = session.query(func.binary(getattr(table_class.c, column_name))).all()

            for row in rows:
                value = row[0]
                if not value:
                    continue
                value = value.decode('utf-8')
                if value not in map_dict:
                    result[value] = supplements[index]
                    index += 1

    return result


def catch_them_all(db_engine):
    email_map, name_map, username_map = make_map_data()

    new_email_map = collect_data(db_engine, email_map, EMAIL_COLUMNS)
    new_name_map = collect_data(db_engine, name_map, NAME_COLUMNS)
    new_username_map = collect_data(db_engine, username_map, USERNAME_COLUMNS)

    email_diff = set(new_email_map) - set(email_map)
    username_diff = set(new_username_map) - set(username_map)
    name_diff = set(new_name_map) - set(name_map)

    print(repr(list(email_diff)))
    print(repr(list(username_diff)))
    print(repr(list(name_diff)))



if __name__ == '__main__':
    main()

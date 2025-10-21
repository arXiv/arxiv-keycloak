import argparse
import hashlib
import json
import os
import time

from arxiv.auth.legacy.passwords import hash_password
from sqlalchemy import func, Engine, Table, update, text, select
from sqlalchemy.exc import IntegrityError

from load_test_data import instantiate_db_engine
from arxiv.db.models import TapirUser, TapirUsersPassword, TapirNickname
from arxiv.db import Base, LaTeXMLBase
from sqlalchemy.orm import Session

from thirdparty.random_name_generator import random_names
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

EMAIL_COLUMNS = [
    ("tapir_users", "email"),
    ("arXiv_admin_metadata","submitter_email"),
    ("arXiv_bib_feeds","email_errors"),
    ("tapir_email_change_tokens", "old_email"),
    ("tapir_email_change_tokens", "new_email"),
    ("tapir_email_log", "email"),
]

USERNAME_COLUMNS = [
    ("arXiv_admin_log","username",),
    ("arXiv_reject_session_usernames","username"),
]


NAME_COLUMNS = [
    ("arXiv_admin_metadata", "submitter_name"),
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


def main(load_schema: bool = False, load_data: bool = True) -> None:
    db_engine, tables = instantiate_db_engine()
    #make_user_remap_data(db_engine)
    smash_passwords(db_engine)
    #remap_user(db_engine)
    #seek_and_destroy(db_engine, tables)

    # change_user_names(db_engine)


# One time use code for fixing up the names/emails
# def merge_remaps():
#     with open("nogoog-users-map.json") as infile1:
#         in1 = json.load(infile1)
#
#     with open("mapped-user.json") as infile2:
#         in2 = json.load(infile2)
#
#     for u1, u2 in zip(in1, in2):
#         u1['first_name'][0] = u2['first_name'][0]
#         u1['last_name'][0] = u2['last_name'][0]
#         u1['email'][0] = u2['email'][0]
#
#     with open("users-map.json", "w") as outfile:
#         json.dump(in1, outfile, indent=4)


def make_map_data():

    with open("users-map.json") as infile:
        users = json.load(infile)

    email_map = {}
    name_map = {}
    username_map = {}

    for user in users:
        orig_first_name = user['first_name'][0]
        orig_last_name = user['last_name'][0]
        orig_email = user['email'][0]

        email_map[orig_email] = user['email'][1]

        orig_full_name = f"{orig_first_name} {orig_last_name}"
        mapped_full_name = f"{user['first_name'][1]} {user['last_name'][1]}"
        name_map[orig_full_name] = mapped_full_name

        orig_username = user['username'][0]
        username_map[orig_username] = user['username'][1]

    return email_map, name_map, username_map


def get_mysql_table_charset(db_engine, table_name, database_name = "arXiv"):
    query = text("""
        SELECT TABLE_COLLATION
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = :database_name
        AND TABLE_NAME = :table_name;
    """)

    with db_engine.connect() as connection:
        result = connection.execute(query, {"database_name": database_name, "table_name": table_name})
        table_collation = result.scalar()  # Example result: utf8mb4_unicode_ci

    if table_collation:
        # Extract character set from collation (e.g., utf8mb4_unicode_ci -> utf8mb4)
        charset = table_collation.split('_')[0]
        return charset

    return None  # Return None if no result is found


def replace_data(db_engine, map_dict, cleansing_targets):
    Base.metadata.reflect(db_engine)

    with Session(db_engine) as session:
        for table_name, column_name in cleansing_targets:
            table_class: Table = Base.metadata.tables[table_name]
            table_charset = get_mysql_table_charset(db_engine, table_name)
            if table_charset:
                is_utf8_table = table_charset.find('utf8') != -1
            # column_index = table_class.columns.keys().index(column_name)

            primary_keys = [col.name for col in table_class.primary_key.columns][:1]
            if not primary_keys:
                raise ValueError(f"Table {table_name} has no primary key, cannot update reliably.")

            if is_utf8_table:
                rows = session.query(getattr(table_class.c, column_name), getattr(table_class.c, primary_keys[0])).all()
            else:
                rows = session.query(func.binary(getattr(table_class.c, column_name)), getattr(table_class.c, primary_keys[0])).all()

            for idx, row in enumerate(rows):
                value = row[0]
                if not value:
                    continue

                if not is_utf8_table:
                    value = value.decode('utf-8')

                if value not in map_dict:
                    raise ValueError(f"Table {table_name} has no value for {value}.")

                new_value = map_dict[value]
                filters = {pk: getattr(row, pk) for pk in primary_keys}
                bits = new_value if is_utf8_table else new_value.encode('utf-8').decode('latin-1')
                stmt = (
                    update(table_class)
                    .where(*(table_class.c[pk] == filters[pk] for pk in primary_keys))
                    .values({column_name: bits})
                )
                print(f"{idx}:" + repr(stmt))
                try:
                    session.execute(stmt)
                except IntegrityError as exc:
                    stmt2 = select(table_class).where(getattr(table_class.c, column_name) == bits)
                    try:
                        diag = session.execute(stmt2).all()
                        print(f"{idx}:" + repr(diag))
                    except Exception:
                        pass
                    raise exc
                pass
        session.commit()


def collect_data(db_engine, map_dict, cleansing_targets, supplements) -> dict:
    Base.metadata.reflect(db_engine)
    result = map_dict.copy()
    used = result.copy()
    used.update({value: value for _key, value in map_dict.items()})

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
                used[value] = value

            rows = session.query(func.binary(getattr(table_class.c, column_name))).all()
            for row in rows:
                value = row[0]
                if not value:
                    continue
                value = value.decode('utf-8')

                if value not in map_dict:
                    while supplements[index] in result or supplements[index] in used:
                        index += 1
                    result[value] = supplements[index]
                    used[supplements[index]] = supplements[index]
                    index += 1


    return result


def seek_and_destroy(db_engine, tables):
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

    replace_data(db_engine, new_email_map, EMAIL_COLUMNS)
    replace_data(db_engine, new_name_map, NAME_COLUMNS)
    replace_data(db_engine, new_username_map, USERNAME_COLUMNS)


def change_user_names(db_engine):
    index = 0
    with Session(db_engine) as session:
        user: TapirUser
        nickname: TapirNickname
        for user, nickname in session.query(TapirUser, TapirNickname).filter(
                TapirNickname.user_id == TapirUser.user_id).all():
            nickname.nickname = "user%04d" % index
            index += 1
            session.add(nickname)
        session.commit()
    pass


def make_user_remap_data(db_engine: Engine) -> None:
    """
    """
    random_names ="../tests/data/random-names.json"

    with open(random_names) as substitution_fd:
        substitutions = json.load(substitution_fd)

    users = []
    with Session(db_engine) as session:
        for user_id, first_name, last_name, suffix_name, email, username in session.query(
                TapirUser.user_id,
                func.binary(TapirUser.first_name),
                func.binary(TapirUser.last_name),
                TapirUser.suffix_name,
                TapirUser.email,
                TapirNickname.nickname,
        ).outerjoin(TapirNickname, TapirUser.user_id == TapirNickname.user_id).all():
            try:
                users.append({
                    'user_id': user_id,
                    'first_name': first_name.decode('utf-8'),
                    'last_name': last_name.decode('utf-8'),
                    'suffix_name': suffix_name,
                    'email': email,
                    'username': username,
                })
            except UnicodeDecodeError:
                print(f"{first_name!r}  {last_name!r}  {email!r}")
                pass

    mapped_users = []
    for user, sub in zip(users, substitutions):
        mapped_users.append({
            'user_id': user['user_id'],
            'first_name': [user['first_name'], sub['first_name']],
            'last_name': [user['last_name'], sub['last_name']],
            'suffix_name': [user['suffix_name'], user['suffix_name']],
            'email': [user['email'], sub['email'].lower()],
            'username': [user['username'], "user%04d" % len(mapped_users)],
        })

    with open("users-map.json", "w") as outfile:
        json.dump(mapped_users, outfile, indent=4)

    pass


def remap_user(db_engine: Engine) -> None:
    """
    """
    random_names ="../tests/data/random-names.json"

    with open(random_names) as substitution_fd:
        substitutions = json.load(substitution_fd)

    # load submissions
    index = 0
    with Session(db_engine) as session:
        for user in session.query(TapirUser).all():
            randomized = substitutions[index]
            user.first_name = randomized['first_name'].encode('utf-8').decode("latin-1"),
            user.last_name = randomized['last_name'].encode('utf-8').decode("latin-1"),
            user.email = randomized['email'].lower()
            user.joined_ip_num = "127.0.0.1"
            user.joined_remote_host = "example.com"
            user.tracking_cookie = ""
            session.add(user)
            index += 1
        session.commit()
    pass


def smash_passwords(db_engine: Engine) -> None:
    with Session(db_engine) as session:
        user_password: TapirUsersPassword
        hasher = hashlib.md5()

        # Process in batches of 1000
        batch_size = 100

        for i in range(1, 1000000000, batch_size):
            users = session.query(TapirUser).filter(TapirUser.user_id.in_(range(i, i+batch_size))).all()
            if len(users) == 0:
                break

            passwords = session.query(TapirUsersPassword).filter(TapirUsersPassword.user_id.in_(range(i, i+batch_size))).all()
            if len(passwords) == 0:
                break

            # Process current batch
            for user, user_password in zip(users, passwords):
                hasher.update((user.email + str(time.process_time())).encode('utf-8'))
                user_password.password_enc = hash_password(hasher.hexdigest())

            # Commit the current batch
            session.commit()


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description="A command-line tool with boolean flags.")
    # parser.add_argument('--load-schema', action='store_true', help="Load the schema.")
    # parser.add_argument('--load-test-data', action='store_true', help="Load test data.")
    # args = parser.parse_args()

    main()

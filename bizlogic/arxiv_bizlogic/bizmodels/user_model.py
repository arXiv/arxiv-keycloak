"""arXiv user model

This is more abstract than using raw SQLAlchemy table based models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List

from sqlalchemy import select, case, exists, cast, LargeBinary, func, inspect, update
from sqlalchemy.orm import Session
from sqlalchemy.engine.row import Row
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic, OrcidIds, TapirPolicyClass)
from logging import getLogger
from ..sqlalchemy_helper import update_model_fields

logger = getLogger(__name__)

ACCOUNT_MANAGEMENT_FIELDS = {
    'first_name', 'flag_approved', 'flag_banned', 'flag_can_lock', 'flag_deleted', 'flag_edit_system', 'flag_edit_users',
    'flag_internal', 'joined_date', 'joined_ip_num', 'joined_remote_host', 'last_name', 'policy_class',  'suffix_name',
}

_tapir_user_utf8_fields_ = ["first_name", "last_name", "suffix_name", "email"]
_demographic_user_utf8_fields_ = ["url", "affiliation", ]

TAPIR_USER_EMPTY_DATA = {
    "share_first_name": 1,
    "share_last_name": 1,
    "email": "",
    "share_email": 1,
    "email_bouncing": 0,
    "policy_class": 0,
    "joined_date": datetime.now(tz=timezone.utc), # overwrite
    "joined_ip_num": "128.0.0.1", # overwrite
    "joined_remote_host": "localhost", # overwrite
    "flag_internal": 0,
    "flag_edit_users": 0,
    "flag_edit_system": 0,
    "flag_email_verified": 0,
    "flag_approved": 1,
    "flag_deleted": 0,
    "flag_banned": 0,
    "flag_wants_email": 0,
    "flag_html_email": 0,
    "tracking_cookie": "",
    "flag_allow_tex_produced": 0,
    "flag_can_lock": 0,
}

ARXIV_DEMOGRAPHIC_EMTPY_DATA = {
    "user_id": 0, # You need to copy and overwrite
    "country": "",
    "affiliation": "",
    "url": "",
    "type": None,
    "archive": None,
    "subject_class": None,
    "original_subject_classes": "",
    "flag_group_physics": None,
    "flag_group_math": 0,
    "flag_group_cs": 0,
    "flag_group_nlin": 0,
    "flag_proxy": 0,
    "flag_journal": 0,
    "flag_xml": 0,
    "dirty": 0,
    "flag_group_test": 0,
    "flag_suspect": 0,
    "flag_group_q_bio": 0,
    "flag_group_q_fin": 0,
    "flag_group_stat": 0,
    "flag_group_eess": 0,
    "flag_group_econ": 0,
    "veto_status": "ok"
}


USER_MODEL_DEFAULTS = {
    "policy_class": 2,
    "joined_remote_host": "",
    "tracking_cookie": "",
    "share_first_name": True,
    "share_last_name": True,
    "share_email": 8,
    "email_bouncing": False,
    "flag_internal": False,
    "flag_edit_users": False,
    "flag_edit_system": False,
    "flag_email_verified": False,
    "flag_approved": True,
    "flag_deleted": False,
    "flag_banned": False,
    "flag_wants_email": False,
    "flag_html_email": False,
    "flag_allow_tex_produced": False,
    "flag_can_lock": False,
    "dirty": False,
    "veto_status": "ok",
    "flag_proxy": False,
}


def dict_merge(dict1: dict, dict2: dict) -> dict:
    for key, value in dict2.items():
        if key in dict1 and value is not None:
            dict1[key] = value
    return dict1


class VetoStatusEnum(str, Enum):
    ok = 'ok'
    no_endorse = 'no-endorse'
    no_upload = 'no-upload'
    no_replace = 'no-replace'


def list_mod_cats_n_arcs(session: Session, user_id: int) -> tuple[list[str], list[str]]:
    list_mod = (
        select(t_arXiv_moderators.c.archive, t_arXiv_moderators.c.subject_class)
        .where(t_arXiv_moderators.c.user_id == user_id)
    )
    mods = session.execute(list_mod).fetchall()

    mod_cats = [f"{mod.archive}.{mod.subject_class}" for mod in mods if mod.archive and mod.subject_class]
    mod_archives = [row.archive for row in mods if row.archive and (not row.subject_class)]
    return mod_cats, mod_archives


class UserModel(BaseModel):
    class Config:
        from_attributes = True

    id: Optional[int] = None
    email: str
    first_name: str
    last_name: str
    suffix_name: Optional[str] = None
    share_first_name: bool = True
    share_last_name: bool = True
    username: Optional[str] = None
    share_email: int = 8
    email_bouncing: bool = False
    policy_class: int
    joined_date: datetime
    joined_ip_num: Optional[str] = None
    joined_remote_host: str
    flag_internal: bool = False
    flag_edit_users: bool = False
    flag_edit_system: bool = False
    flag_email_verified: bool = False
    flag_approved: bool = True
    flag_deleted: bool = False
    flag_banned: bool = False
    flag_wants_email: Optional[bool] = None
    flag_html_email: Optional[bool] = None
    tracking_cookie: Optional[str] = None
    flag_allow_tex_produced: Optional[bool] = None
    flag_can_lock: Optional[bool] = None

    # From Demographic
    country: Optional[
        str] = None  # = mapped_column(String(2), nullable=False, index=True, server_default=FetchedValue())
    affiliation: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    url: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    type: Optional[int] = None  # = mapped_column(SmallInteger, index=True)
    archive: Optional[str] = None  # = mapped_column(String(16))
    subject_class: Optional[str] = None  # = mapped_column(String(16))
    original_subject_classes: str  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    flag_group_physics: Optional[int] = None  # = mapped_column(Integer, index=True)
    flag_group_math: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_cs: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_nlin: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_proxy: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_journal: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_xml: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    dirty: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_test: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_suspect: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_bio: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_fin: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_stat: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_eess: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_econ: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    veto_status: Optional[
        VetoStatusEnum] = None  # Mapped[Literal['ok', 'no-endorse', 'no-upload', 'no-replace']] = mapped_column(Enum('ok', 'no-endorse', 'no-upload', 'no-replace'), nullable=False, server_default=text("'ok'"))

    flag_is_mod: Optional[bool] = None
    moderated_categories: Optional[List[str]] = None
    moderated_archives: Optional[List[str]] = None

    tapir_policy_classes: Optional[List[int]] = None

    orcid_id: Optional[str] = None

    @field_validator('first_name', 'last_name', 'suffix_name', 'username', 'country', 'affiliation', 'url',
                     'archive', 'subject_class', 'original_subject_classes', 'orcid_id',)
    @classmethod
    def strip_field_value(cls, value: str | None) -> str | None:
        return value.strip() if value else value


    @staticmethod
    def base_select(session: Session):
        """
        mod_subquery = select(
            func.concat(t_arXiv_moderators.c.user_id, "+",
                        t_arXiv_moderators.c.archive, "+",
                        t_arXiv_moderators.c.subject_class)
        ).where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)

        mod_cats_subquery = (
            select(
                func.group_concat(
                    func.concat(
                        t_arXiv_moderators.c.archive, ".", t_arXiv_moderators.c.subject_class
                    ).op('ORDER BY')(t_arXiv_moderators.c.archive, t_arXiv_moderators.c.subject_class)
                )
            )
            .where(
                t_arXiv_moderators.c.user_id == TapirUser.user_id,
                t_arXiv_moderators.c.archive.isnot(None),
                t_arXiv_moderators.c.subject_class.isnot(None),
                t_arXiv_moderators.c.subject_class != ""
            )
            .correlate(TapirUser)
            .scalar_subquery()
        )

        mod_archives_subquery = (
            select(
                func.group_concat(
                    t_arXiv_moderators.c.archive.op('ORDER BY')(t_arXiv_moderators.c.archive)
                )
            )
            .where(
                t_arXiv_moderators.c.user_id == TapirUser.user_id,
                t_arXiv_moderators.c.archive.isnot(None),
                (t_arXiv_moderators.c.subject_class.is_(None)) | (t_arXiv_moderators.c.subject_class == "")
            )
            .correlate(TapirUser)
            .scalar_subquery()
        )
        """

        return session.query(
            TapirUser.user_id.label("id"),
            cast(TapirUser.email, LargeBinary).label("email"),
            cast(TapirUser.first_name, LargeBinary).label("first_name"),
            cast(TapirUser.last_name, LargeBinary).label("last_name"),
            cast(TapirUser.suffix_name, LargeBinary).label("suffix_name"),
            TapirUser.share_first_name,
            TapirUser.share_last_name,
            TapirUser.share_email,
            TapirUser.email_bouncing,
            TapirUser.policy_class,
            TapirUser.joined_date,
            TapirUser.joined_ip_num,
            TapirUser.joined_remote_host,
            TapirUser.flag_internal,
            TapirUser.flag_edit_users,
            TapirUser.flag_edit_system,
            TapirUser.flag_email_verified,
            TapirUser.flag_approved,
            TapirUser.flag_deleted,
            TapirUser.flag_banned,
            TapirUser.flag_wants_email,
            TapirUser.flag_html_email,
            TapirUser.tracking_cookie,
            TapirUser.flag_allow_tex_produced,
            TapirUser.flag_can_lock,
            # mod_subquery.label("moderator_id"),
            Demographic.country,
            cast(Demographic.affiliation, LargeBinary).label("affiliation"),
            cast(Demographic.url, LargeBinary).label("url"),
            Demographic.type,
            Demographic.archive,
            Demographic.subject_class,
            Demographic.original_subject_classes,
            Demographic.flag_group_physics,
            Demographic.flag_group_math,
            Demographic.flag_group_cs,
            Demographic.flag_group_nlin,
            Demographic.flag_proxy,
            Demographic.flag_journal,
            Demographic.flag_xml,
            Demographic.dirty,
            Demographic.flag_group_test,
            Demographic.flag_suspect,
            Demographic.flag_group_q_bio,
            Demographic.flag_group_q_fin,
            Demographic.flag_group_stat,
            Demographic.flag_group_eess,
            Demographic.flag_group_econ,
            Demographic.veto_status,
        ).outerjoin(Demographic, TapirUser.user_id == Demographic.user_id)

    @property
    def is_admin(self) -> bool:
        return self.flag_edit_users or self.flag_edit_system

    @staticmethod
    def map_to_row_data(from_fields: dict, to_fields: List[str] | dict, utf8_fields: List[str]) -> dict:
        """Convert given thing ready for database data.
        utf8_fields turns the data into UTF-8, and pretend to be latin-1.
        """
        data = {}
        for field in to_fields:
            from_field = "id" if field == "user_id" else field
            if from_field in from_fields:
                data[field] = from_fields[from_field]
            elif from_field in USER_MODEL_DEFAULTS:
                data[field] = USER_MODEL_DEFAULTS[from_field]
        for field in utf8_fields:
            if data[field] and isinstance(data[field], str):
                data[field] = data[field].encode("utf-8")
        return data

    @staticmethod
    def to_model(user: UserModel | Row | dict, session: Optional[Session] = None) -> UserModel:
        """
        Given data to user model data.
        :param user:  DB row, dict or UserModel.
        :param session: SQLAlchemy db session
        :return: result: UserModel data
        """
        # If the incoming is already a dict, to_model is equivalet of calling model_validate
        if isinstance(user, dict):
            result = UserModel.model_validate(user)
        elif isinstance(user, UserModel):
            # This is just a copy
            return UserModel.model_validate(user.model_dump())
        elif isinstance(user, Row):
            row = user._asdict()
            for field in _tapir_user_utf8_fields_ + _demographic_user_utf8_fields_:
                if row[field] is None:
                    continue
                if isinstance(row[field], bytes):
                    row[field] = row[field].decode("utf-8") if row[field] is not None else None
                elif isinstance(row[field], str):
                    logger.warning(f"Field {field} is unexpectedly string. value = '{row[field]}'. You may need to fix it")
                    pass
                else:
                    raise ValueError(f"Field {field} needs to be BLOB access")
            result = UserModel.model_validate(row)
        else:
            raise ValueError("Not Row, UserModel or dict")

        if session:
            result.moderated_categories, result.moderated_archives = list_mod_cats_n_arcs(session, result.id)
            result.flag_is_mod = session.query(exists().where(t_arXiv_moderators.c.user_id == result.id)).scalar()
            nicks = session.query(TapirNickname.nickname).where(TapirNickname.user_id == result.id).all()
            if nicks and len(nicks) > 0:
                result.username = nicks[0].nickname
            orcid = session.query(OrcidIds).where(OrcidIds.user_id == result.id).all()
            if orcid and len(orcid) > 0:
                result.orcid_id = orcid[0].orcid

        return result


    @staticmethod
    def one_user(session: Session, user_id: str) -> UserModel | None:
        """
        Get one user model data from user id (aka int primary key)
        :param session: DB session
        :param user_id:
        :return:
        """
        user = UserModel.base_select(session).filter(TapirUser.user_id == user_id).one_or_none()
        if user is None:
            return None
        return UserModel.to_model(user, session=session)

    @staticmethod
    def one_user_from_username(session: Session, username: str) -> UserModel | None:
        """
        Get one user model data from username via TapirNickname.
        :param session:
        :param username:
        :return:
        """
        nick: TapirNickname | None = session.query(TapirNickname).filter(
            TapirNickname.nickname == username).one_or_none()
        if nick is None:
            return None
        return UserModel.one_user(session, str(nick.user_id))

    @staticmethod
    def _update_model_fields(session: Session, db_object, model_class, data: dict, user_id: int,
                            skip_fields: set = None) -> bool:
        """
        Helper function to update database model fields with type conversion and UTF-8 handling.

        :param session: SQLAlchemy session
        :param db_object: Database object instance to update
        :param model_class: SQLAlchemy model class for column metadata
        :param data: Dictionary of field values to update
        :param user_id: User ID for update queries
        :param skip_fields: Set of field names to skip during update
        """

        inspector = inspect(model_class)
        columns = {column.key for column in model_class.__mapper__.column_attrs}

        if skip_fields is not None:
            for field in skip_fields:
                if field in columns:
                    columns.remove(field)

        return update_model_fields(session, db_object, data, columns, primary_key_field="user_id", primary_key_value=user_id)


    @staticmethod
    def _upsert_user(session: Session, user: dict) -> TapirUser | None:
        """
        Insert or update user data (TapirUser and Demographic)
        This is intended for "public info" part of user data such as names. Admin/authz is not covered here.
        NOTE: No password record is created when the user is created
        :param session: DB session
        :param user: DB ready data
        :return:
        """

        # Handle TapirUser
        tapir_user_columns = {column.key: column for column in TapirUser.__mapper__.column_attrs}
        data = UserModel.map_to_row_data(user, list(tapir_user_columns.keys()), _tapir_user_utf8_fields_)
        user_id = data.get("user_id")
        # Upsert user does not touch following fields
        skip_fields = {
            "user_id",
            "share_first_name",
            "share_last_name",
            "email",
            "share_email",
            "email_bouncing",
            "policy_class",
            "joined_date",
            "joined_ip_num",
            "joined_remote_host",
            "flag_internal",
            "flag_edit_users",
            "flag_edit_system",
            "flag_email_verified",
            "flag_approved",
            "flag_deleted",
            "flag_banned",
            "flag_wants_email",
            "flag_html_email",
            "tracking_cookie",
            "flag_allow_tex_produced",
            "flag_can_lock",
            "tracking_cookie",
            "flag_group_test"
        }

        if user_id is None:
            # FIXME: TapirNickname needs to be created
            min_data = TAPIR_USER_EMPTY_DATA.copy()
            min_data.update(
                {
                "joined_date": datetime.now(tz=timezone.utc),
                "joined_ip_num": data.get("joined_ip_num"),
                "joined_remote_host": data.get("joined_remote_host"),
                })
            db_user = TapirUser(**min_data) # Make an emtpy and fill up later
            session.add(db_user)
            session.flush()
            session.refresh(db_user)
            user_id = db_user.user_id

            db_nick = TapirNickname(
                nickname=data.get("username"),
                user_id=user_id,
                user_seq=0,
                flag_valid=1,
                role=0,
                policy=0,
                flag_primary=1)
            session.add(db_nick)
            session.flush()
            session.refresh(db_nick)
        else:
            db_user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
            if db_user is None:
                raise ValueError(f"User {user_id} not found")

        updated = UserModel._update_model_fields(
            session, db_user, TapirUser, data, user_id,
            skip_fields=skip_fields
        )

        if updated:
            logger.info(f"_upsert_user: Updated user {user_id}")

        # Handle Demographic
        to_demographics_fields = set([column.key for column in Demographic.__mapper__.column_attrs])
        demographic_data = UserModel.map_to_row_data(user, to_demographics_fields, _demographic_user_utf8_fields_)
        demographic_data["user_id"] = db_user.user_id

        db_demographic = session.query(Demographic).filter(Demographic.user_id == db_user.user_id).one_or_none()
        if db_demographic is None:
            demo_data = ARXIV_DEMOGRAPHIC_EMTPY_DATA.copy()
            demo_data.update({
                "user_id": db_user.user_id,
            })
            db_demographic = Demographic(**demo_data)
            session.add(db_demographic)
            session.flush()
            session.refresh(db_demographic)
        # Use the refactored helper function
        updated2 = UserModel._update_model_fields(
            session, db_demographic, Demographic, demographic_data, db_user.user_id,
            skip_fields={"user_id"}
        )
        if updated2:
            logger.info(f"_upsert_user: Updated user demographic {user_id}")
        return db_user

    @staticmethod
    def create_user(session: Session, user_model: UserModel) -> TapirUser | None:
        """
        Creates a user model data on DB. No password or TapirNickname created/updated
        :param session:
        :param user_model:
        :return:
        """
        if not user_model.first_name:
            raise ValueError("Must have first_name to create user")
        if not user_model.last_name:
            raise ValueError("Must have last_name to create user")
        return UserModel._upsert_user(session, user_model.model_dump())

    @staticmethod
    def update_user(session: Session, user_model: UserModel) -> TapirUser | None:
        """
        Updates a user model data on DB.
        :param session:
        :param user_model:
        :return:
        """
        if user_model.id is not None:
            existing = UserModel.one_user(session, user_model.id)
            if existing is None:
                raise ValueError("User not found")
        else:
            raise ValueError("Must have first_name to update")
        data = existing.model_dump()
        for key, value in user_model.model_dump(exclude_unset=True, exclude_defaults=True).items():
            data[key] = value
        return UserModel._upsert_user(session, data)


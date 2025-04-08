"""arXiv user model

This is more abstract than using raw SQLAlchemy table based models
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List

from sqlalchemy import select, case, exists, cast, LargeBinary
from sqlalchemy.orm import Session
from sqlalchemy.engine.row import Row
from pydantic import BaseModel

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic, OrcidIds)
from logging import getLogger

logger = getLogger(__name__)

_tapir_user_utf8_fields_ = ["first_name", "last_name", "suffix_name", "email"]
_demographic_user_utf8_fields_ = ["url", "affiliation", ]


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
    username: str
    share_email: int = 8
    email_bouncing: bool = False
    policy_class: int
    joined_date: int
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

    tapir_policy_classes: Optional[List[int]] = None

    orcid: Optional[str] = None

    @staticmethod
    def base_select(session: Session):
        is_mod_subquery = exists().where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        nick_subquery = select(TapirNickname.nickname).where(TapirUser.user_id == TapirNickname.user_id).correlate(
            TapirUser).limit(1).scalar_subquery()
        """
        mod_subquery = select(
            func.concat(t_arXiv_moderators.c.user_id, "+",
                        t_arXiv_moderators.c.archive, "+",
                        t_arXiv_moderators.c.subject_class)
        ).where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        """

        return (session.query(
            TapirUser.user_id.label("id"),
            cast(TapirUser.email, LargeBinary).label("email"),
            cast(TapirUser.first_name, LargeBinary).label("first_name"),
            cast(TapirUser.last_name, LargeBinary).label("last_name"),
            cast(TapirUser.suffix_name, LargeBinary).label("suffix_name"),
            TapirUser.share_first_name,
            TapirUser.share_last_name,
            nick_subquery.label("username"),
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
            case(
                (is_mod_subquery, True),  # Pass each "when" condition as a separate positional argument
                else_=False
            ).label("flag_is_mod"),
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
            OrcidIds.orcid)
                .outerjoin(Demographic, TapirUser.user_id == Demographic.user_id)
                .outerjoin(OrcidIds, TapirUser.user_id == OrcidIds.user_id))

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
            data[field] = data[field].encode("utf-8").decode('iso-8859-1')
        return data

    @staticmethod
    def to_model(user: UserModel | Row | dict) -> UserModel:
        """
        Given data to user model data.
        :param user:  DB row, dict or UserModel.
        :return:
        """
        # If the incoming is already a dict, to_model is equivalet of calling model_validate
        if isinstance(user, dict):
            return UserModel.model_validate(user)
        elif isinstance(user, UserModel):
            return UserModel.model_validate(user.model_dump())
        elif isinstance(user, Row):
            row = user._asdict()
        else:
            raise ValueError("Not Row, UserModel or dict")

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
        return UserModel.model_validate(row)

    @staticmethod
    def one_user(db: Session, user_id: str) -> UserModel | None:
        """
        Get one user model data from user id (aka int primary key)
        :param db: DB session
        :param user_id:
        :return:
        """
        user = UserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
        if user is None:
            return None
        return UserModel.to_model(user)

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
    def _upsert_user(session: Session, user: dict) -> TapirUser | None:
        """
        Insert or update user data (TapirUser and Demographic)
        NOTE: No password or TapirNickname created/updated
        :param session: DB session
        :param user: DB ready data
        :return:
        """

        tapir_user_fields = set([column.key for column in TapirUser.__mapper__.column_attrs])
        data = UserModel.map_to_row_data(user, tapir_user_fields, _tapir_user_utf8_fields_)
        if data.get("user_id") is None:
            db_user = TapirUser(**data)
            session.add(db_user)
            session.flush()
            session.refresh(db_user)
        else:
            db_user = session.query(TapirUser).filter(TapirUser.user_id == data.get("user_id")).one_or_none()
            if db_user is None:
                raise ValueError("User not found")
            for field in tapir_user_fields:
                # Changing of email needs a special care
                if field not in ["user_id", "email"]:
                    setattr(db_user, field, data[field])

        to_demographics_fields = set([column.key for column in Demographic.__mapper__.column_attrs])
        demographic_data = UserModel.map_to_row_data(user, to_demographics_fields, _demographic_user_utf8_fields_)
        demographic_data["user_id"] = db_user.user_id

        db_demographic = session.query(Demographic).filter(Demographic.user_id == db_user.user_id).one_or_none()
        if db_demographic is None:
            db_demographic = Demographic(**demographic_data)
            session.add(db_demographic)
        else:
            for field in to_demographics_fields:
                if field not in ["user_id"]:
                    setattr(db_demographic, field, demographic_data[field])
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

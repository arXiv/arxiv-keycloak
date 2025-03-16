"""arXiv user routes."""
from typing import Optional, List

from sqlalchemy import select, case, exists, cast, LargeBinary
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic)


class UserModel(BaseModel):
    class Config:
        from_attributes = True

    id: int
    email: str
    first_name: str
    last_name: str
    suffix_name: str
    share_first_name: int
    share_last_name: int
    username: str
    share_email: int
    email_bouncing: bool
    policy_class: int
    joined_date: int
    joined_ip_num: Optional[str] = None
    joined_remote_host: str
    flag_internal: bool
    flag_edit_users: bool
    flag_edit_system: bool
    flag_email_verified: bool
    flag_approved: bool
    flag_deleted: bool
    flag_banned: bool
    flag_wants_email: Optional[bool] = None
    flag_html_email: Optional[bool] = None
    tracking_cookie: str
    flag_allow_tex_produced: Optional[bool] = None
    flag_can_lock: Optional[bool] = None

    # From Demographic
    country: Optional[str] = None  # = mapped_column(String(2), nullable=False, index=True, server_default=FetchedValue())
    affiliation: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    url: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    type: Optional[int] = None  # = mapped_column(SmallInteger, index=True)
    archive: Optional[str] = None  # = mapped_column(String(16))
    subject_class: Optional[str] = None  # = mapped_column(String(16))
    original_subject_classes: str  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    flag_group_physics: Optional[int] = None  # = mapped_column(Integer, index=True)
    flag_group_math: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_cs: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_nlin: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_proxy: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_journal: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_xml: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    dirty: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_test: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_suspect: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_bio: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_fin: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_stat: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_eess: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_econ: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    veto_status: Optional[str] = None  # Mapped[Literal['ok', 'no-endorse', 'no-upload', 'no-replace']] = mapped_column(Enum('ok', 'no-endorse', 'no-upload', 'no-replace'), nullable=False, server_default=text("'ok'"))

    flag_is_mod: Optional[bool] = None

    tapir_policy_classes: Optional[List[int]] = None

    @staticmethod
    def base_select(db: Session):
        is_mod_subquery = exists().where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        nick_subquery = select(TapirNickname.nickname).where(TapirUser.user_id == TapirNickname.user_id).correlate(TapirUser).limit(1).scalar_subquery()
        """
        mod_subquery = select(
            func.concat(t_arXiv_moderators.c.user_id, "+",
                        t_arXiv_moderators.c.archive, "+",
                        t_arXiv_moderators.c.subject_class)
        ).where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        """

        return (db.query(
            TapirUser.user_id.label("id"),
            TapirUser.email,
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
            Demographic.url,
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
            Demographic.veto_status
        ).outerjoin(Demographic, TapirUser.user_id == Demographic.user_id)
        )

    @property
    def is_admin(self) -> bool:
        return self.flag_edit_users or self.flag_edit_system


    @staticmethod
    def to_model(user: "UserModel") -> "UserModel":
        row = user._asdict()
        for field in ["first_name", "last_name", "suffix_name", "affiliation"]:
            row[field] = row[field].decode("utf-8") if row[field] is not None else None
        return UserModel.model_validate(row)
    pass

    @staticmethod
    def one_user(db: Session, user_id: int) -> "UserModel":
        user = UserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
        if user is None:
            return None
        return UserModel.to_model(user)

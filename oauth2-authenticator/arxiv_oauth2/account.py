"""Account management"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.db.models import TapirUser, Demographic, Category, TapirNickname

from . import get_current_user_or_none, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

class AccountInfoModel(BaseModel):
    id: int
    oidc_id: Optional[str]
    first_name: str
    last_name: str
    suffix_name: Optional[str]
    country: str
    affiliation: str
    url: Optional[str]
    category: Optional[str]
    groups: List[str]


def to_group_name(group_flag, demographic: Demographic) -> Optional[str]:
    group_name, flag_name = group_flag
    return group_name if hasattr(demographic, flag_name) and getattr(demographic, flag_name) else None


@router.get('/current/info')
async def info(current_user: Optional[ArxivUserClaims] = Depends(get_current_user_or_none),
               session: Session = Depends(get_db)
          ) -> AccountInfoModel:
    """
    Hit the db and get user info
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_data: (TapirUser, TapirNickname, Demographic) = session.query(TapirUser, TapirNickname, Demographic) \
        .join(TapirNickname).join(Demographic) \
        .filter(TapirUser.user_id == current_user.user_id) \
        .first()

    tapir_user = None
    tapir_nickname = None
    demographic = None

    if user_data:
        tapir_user, tapir_nickname, demographic = user_data

    if tapir_user and demographic:
        groups = [to_group_name(group_flag, demographic) for group_flag in Demographic.GROUP_FLAGS]

        category: Optional[Category] = session.query(Category).filter(
            and_(
                Category.archive == demographic.archive,
                Category.subject_class == demographic.subject_class
            )
        ).one_or_none()
        account = AccountInfoModel(
            id = tapir_user.user_id,
            oidc_id = None,
            first_name = tapir_user.first_name,
            last_name = tapir_user.last_name,
            suffix_name = tapir_user.suffix_name,
            country = demographic.country,
            affiliation = demographic.affiliation,
            url = demographic.url,
            category = category.category_name if category else None,
            groups = [group for group in groups if group]
        )
        return account
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

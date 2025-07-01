"""
Migrate user from Tapir to Keycloak without credentials
"""
import random
import string
from arxiv_bizlogic.bizmodels.user_model import UserModel
from fastapi import status, HTTPException
from arxiv.base import logging
from arxiv.db.models import TapirUsersPassword
from arxiv.auth.legacy import passwords
from keycloak import KeycloakAdmin

from .account_biz import (AccountInfoModel, migrate_to_keycloak)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def cold_migrate(kc_admin: KeycloakAdmin, session: Session, user_id: str, client_secret: str, email_verified: bool = False) -> dict:
    """
    Force the issue, and create the account
    I cannot come up with anything better, so here it goes.

    1. Save the current password data
    2. Smash the existing password with temporary password
    3. Using the temp password, migrate the user
    4. Once the migration is complete, restore the original password to Tapir password
    5. Purge the credentials from keycloak so the next login hits legacy auth provider and uses old password

    :param kc_admin:
    :param session:
    :param user_id:
    :param client_secret: request.app.extra['ARXIV_USER_SECRET']
    :param email_verified: bool, default False

    :return: dict of keycloak user
    """

    # client_secret =

    um: UserModel | None = UserModel.one_user(session, str(user_id))  # Use UserModel to get username
    if um is None:
        # This should not happen. The tapir user exists and therefore, this must succeed.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    tapir_password: TapirUsersPassword | None = session.query(TapirUsersPassword).filter(
        TapirUsersPassword.user_id == user_id).one_or_none()
    if tapir_password is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User password does not exist")

    current_password_enc = tapir_password.password_enc
    try:
        temp_password = ''.join(random.choices(string.ascii_letters, k=48))
        tapir_password.password_enc = passwords.hash_password(temp_password)
        session.commit()

        account = AccountInfoModel(
            id=str(um.id),
            email_verified=email_verified,
            email=um.email,
            username=um.username,
            first_name=um.first_name,
            last_name=um.last_name,
        )
        migrate_to_keycloak(kc_admin, account, temp_password, client_secret)
    finally:
        tapir_password.password_enc = current_password_enc
        session.commit()

    credentials = kc_admin.get_credentials(str(user_id))
    for credential in credentials:
        credential_id = credential["id"]
        kc_admin.delete_credential(user_id=str(user_id), credential_id=credential_id)
    return kc_admin.get_user(str(user_id))

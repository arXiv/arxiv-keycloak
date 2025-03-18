"""Contains route information."""

from keycloak import KeycloakAdmin
from arxiv_bizlogic.fastapi_helpers import *


ALGORITHM = "HS256"
KEYCLOAK_ADMIN = 'KEYCLOAK_ADMIN'

def get_keycloak_admin(request: Request) -> KeycloakAdmin:
    return request.app.extra[KEYCLOAK_ADMIN]


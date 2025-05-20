"""
A Python library for communication with ORCID.

This module handles the OAuth2 authentication flow with ORCID,
manages credentials, and provides utilities for working with ORCID IDs.
"""
import dataclasses

from urllib.parse import urlencode
from typing import Optional
from pydantic import BaseModel
from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient


@dataclasses.dataclass
class ArxivOrcidConfig:
    client_id: str
    client_secret: str
    authorize_site: str
    authorize_path: str
    exchange_site: str
    exchange_path: str
    redirect_uri: str
    instance: str
    # errstr: str


class OrcidAuthRequest(BaseModel):
    class Config:
        from_attribute = True

    client_id: str
    response_type: str
    scope: str
    redirect_uri: str
    state: str
    family_names: Optional[str] = None
    given_names: Optional[str] = None
    email: Optional[str] = None


class ArxivORCID(ArxivOidcIdpClient):
    """
    """

    def __init__(self, config: ArxivOrcidConfig):
        """
        Create a new ArxivORCID object.

        Args:
            config: ORCID instance configuration to use.

        """
        self.config = config
        super().__init__(

        )


    @property
    def login_url(self) -> str:
        self._logger.debug(f'login_url: {url}')
        return url


    def authorize_uri(self) -> str:
        """
        Return the URI to redirect the user to start the OAuth process.

        Args:
            scope: Optional, else use default
            redirect_uri: Optional, else use default
            state: Optional, to protect against CSRF
            family_names: Optional, to pre-fill registration
            given_names: Optional, to pre-fill registration
            email: Optional, to select login or pre-fill registration

        Returns:
            Authorization URL for redirecting the user
        """

        self.state = kwargs.get('state')

        qp = OrcidAuthRequest(
            client_id= kwargs.get('client_id', self.config.client_id),
            response_type= 'code',
            scope=kwargs.get('scope', self.scope or '/authenticate'),
            redirect_uri=kwargs.get('redirect_uri', self.config.redirect_uri),
            state= self.state,
            family_names= kwargs.get('family_names'),
            given_names= kwargs.get('given_names'),
            email=kwargs.get('email'))

        site = kwargs.get('site', self.config.authorize_site)
        path = kwargs.get('path', self.config.authorize_path)
        return f"{site}{path}?{urlencode(qp.model_dump(exclude_none=True, exclude_defaults=True))}"


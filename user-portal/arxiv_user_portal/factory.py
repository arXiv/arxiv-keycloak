"""Application factory for user-portal."""

import logging

from flask import Flask
from flask_s3 import FlaskS3
from flask_bootstrap import Bootstrap5

from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

from arxiv.base import Base
from arxiv.base.middleware import wrap

from arxiv.auth import auth
from arxiv.auth.auth.sessions import SessionStore
from arxiv.auth.legacy.util import missing_configs


from arxiv.db import configure_db

from .routes import ui, ownership, endorsement, user, paper
from .legacy.util import init_app as legacy_init_app
from .helpers.arxiv_ce_auth import ArxivCEAuthMiddleware

logging.basicConfig(level=logging.DEBUG)

s3 = FlaskS3()

logger = logging.getLogger(__name__)

csrf = CSRFProtect()

def change_loglevel(pkg:str, level):
    """Change log leve on arxiv-base logging.

    arxiv-base logging isn't quite right in that the handler levels
    don't get updated after they get intitialzied.

    Use this like in the create_web_app function:

        change_loglevel('arxiv.auth.auth', 'DEBUG')
        change_loglevel('admin_webapp.controllers.authentication', 'DEBUG')
        change_loglevel('admin_webapp.routes.ui', 'DEBUG')
    """
    logger_x = logging.getLogger(pkg)
    logger_x.setLevel(level)
    for handler in logger_x.handlers:
        handler.setLevel(level)


def create_web_app() -> Flask:
    """Initialize and configure the admin_webapp application."""

    app = Flask('arxiv-user-portal')
    app.config.from_pyfile('config.py')

    Bootstrap5(app)

    # Don't set SERVER_NAME, it switches flask blueprints to be
    # subdomain aware.  Then each blueprint will only be served on
    # it's subdomain.  This doesn't work with mutliple domains like
    # webN.arxiv.org and arxiv.org. We need to handle both names so
    # that individual nodes can be addresed for diagnotics. Not
    # setting this will allow the flask app to handle both
    # https://web3.arxiv.org/login and https://arxiv.org/login. If
    # this gets set paths that should get handled by the app will 404
    # when the request is made with a HOST that doesn't match
    # SERVER_NAME.
    app.config['SERVER_NAME'] = None

    SessionStore.init_app(app)

    missing = missing_configs(app.config)
    assert not missing

    # Init db
    from arxiv.config import settings
    # from . import CLASSIC_ENGINE_CONFIG_NAME, LATEXML_ENGINE_CONFIG_NAME
    # engine, latexml_engine = configure_db(settings)

    # app.config[CLASSIC_ENGINE_CONFIG_NAME] = engine
    # app.config[LATEXML_ENGINE_CONFIG_NAME] = latexml_engine

    # SQLAlchemy(app, metadata=db.models.Base.metadata)

    # legacy_init_app(app)

    # Auth config
    from auth_config import get_session_meta, ARXIV_CE_SESSION_CONFIG_NAME, CLASSIC_SESSION_CONFIG_NAME, AAA_CONFIG_NAME
    classic_meta, ce_meta, aaa_config = get_session_meta("http://localhost.5100/aaa/token-names", logger)
    app.config[ARXIV_CE_SESSION_CONFIG_NAME] = ce_meta
    app.config[CLASSIC_SESSION_CONFIG_NAME] = classic_meta
    app.config[AAA_CONFIG_NAME] = aaa_config

    app.register_blueprint(ui.blueprint)
    app.register_blueprint(ownership.blueprint)
    app.register_blueprint(endorsement.blueprint)
    app.register_blueprint(user.blueprint)
    app.register_blueprint(paper.blueprint)

    Base(app)
    auth.Auth(app)
    s3.init_app(app)

    csrf.init_app(app)
    [csrf.exempt(view.strip()) for view in app.config['WTF_CSRF_EXEMPT'].split(',')]

    wrap(app, [ArxivCEAuthMiddleware])
    settup_warnings(app)
    return app


def settup_warnings(app):
    if not app.config['SQLALCHEMY_DATABASE_URI'] and not app.config['DEBUG']:
        logger.error("SQLALCHEMY_DATABASE_URI is not set!")

    if not app.config['WTF_CSRF_ENABLED'] and not(app.config['FLASK_DEBUG'] or app.config['DEBUG']):
        logger.warning("CSRF protection is DISABLED, Do not disable CSRF in production")

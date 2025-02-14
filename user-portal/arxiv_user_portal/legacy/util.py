from flask import Flask
import logging
from typing import List
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)
logger.propagate = False


def missing_configs(config) -> List[str]:
    """Returns missing keys for configs  needed in `Flask.config` for legacy auth to work."""
    missing = [key for key in ['CLASSIC_SESSION_HASH', 'SESSION_DURATION', 'CLASSIC_COOKIE_NAME']
               if key not in config]
    return missing


def init_app(app: Flask, db: SQLAlchemy) -> None:
    """Set configuration defaults and attach session to the application."""
    missing = missing_configs(app.config)
    if missing:
        #  Error early if misconfiged, don't catch these, let the stop the app startup
        raise RuntimeError(f"Missing the following configs: {missing}")

    if "sqlalchemy" in app.extensions:
        logger.warning("Skipping init of sqlalchemy since it is already setup")
    else:
        db.init_app(app)

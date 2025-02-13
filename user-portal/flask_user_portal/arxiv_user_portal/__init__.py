"""Contains route information."""
import datetime
import time
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask import Flask


CLASSIC_ENGINE_CONFIG_NAME = 'classic-engine'
LATEXML_ENGINE_CONFIG_NAME = 'latexml-engine'

def datetime_to_epoch(timestamp: datetime.datetime | datetime.date | None,
                      default: datetime.date | datetime.datetime,
                      hour=0, minute=0, second=0) -> int:
    if timestamp is None:
        timestamp = default
    if isinstance(timestamp, datetime.date) and not isinstance(timestamp, datetime.datetime):
        # Convert datetime.date to datetime.datetime at midnight
        timestamp = datetime.datetime.combine(timestamp, datetime.time(hour, minute, second))
    # Use time.mktime() to convert datetime.datetime to epoch time
    return int(time.mktime(timestamp.timetuple()))

VERY_OLDE = datetime.datetime(1981, 1, 1)


def get_db(app:Flask) -> SQLAlchemy:
    """Gets the SQLAlchemy object for the flask app."""
    return app.extensions['sqlalchemy'].db


def get_csrf(app:Flask) -> CSRFProtect:
    """Gets CSRF for the app"""
    return app.extensions['csrf']


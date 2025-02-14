"""Db related functions."""

from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

def get_db(app:Flask) -> SQLAlchemy:
    """Gets the SQLAlchemy object for the flask app."""
    return app.extensions['sqlalchemy'].db

def get_csrf(app:Flask) -> CSRFProtect:
    """Gets CSRF for the app"""
    return app.extensions['csrf']

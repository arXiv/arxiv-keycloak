"""Provides application for development purposes."""
from .factory import create_web_app

app = create_web_app()
# with app.app_context():
#     legacy.create_all()

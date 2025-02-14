"""arXiv user routes."""

from flask import Blueprint, render_template, Response


blueprint = Blueprint('user', __name__, url_prefix='/user')


@blueprint.route('/<int:user_id>', methods=['GET'])
def detail(user_id: int) -> Response:
    """Display a user."""
    return render_template('user/display.html')

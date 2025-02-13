"""arXiv paper ownership routes."""

from flask import Blueprint, render_template, request, \
    Response, make_response

from arxiv.auth.auth.decorators import scoped

from ..controllers.ownership import (
    ownership_detail, ownership_listing, ownership_post, paper_password_post, PaperPasswordForm)


blueprint = Blueprint('ownership', __name__, url_prefix='/ownership')


@blueprint.route('/<int:ownership_id>', methods=['GET', 'POST'])
def display(ownership_id:int) -> Response:
    """Displays a ownership request."""
    if request.method == 'GET':
        return render_template('ownership/display.html',**ownership_detail(ownership_id, None))
    elif request.method == 'POST':
        return render_template('ownership/display.html', **ownership_detail(ownership_id, ownership_post))


@blueprint.route('/pending', methods=['GET'])
def pending() -> Response:
    """Pending ownership requests."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    data = ownership_listing('pending', per_page, page, 0)
    data['title'] = "Ownership Reqeusts: Pending"
    return render_template('ownership/list.html',
                           **data)


@blueprint.route('/accepted', methods=['GET'])
def accepted() -> Response:
    """Accepted ownership requests."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    days_back = args.get('days_back', default=7, type=int)

    data = ownership_listing('accepted', per_page, page, days_back=days_back)
    data['title'] = f"Ownership Reqeusts: accepted last {days_back} days"
    return render_template('ownership/list.html',
                           **data)


@blueprint.route('/rejected', methods=['GET'])
def rejected() -> Response:
    """Rejected ownership reqeusts."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    days_back = args.get('days_back', default=7, type=int)

    data = ownership_listing('rejected', per_page, page, days_back=days_back)
    data['title'] = f"Ownership Reqeusts: Rejected last {days_back} days"
    return render_template('ownership/list.html',
                           **data)

@scoped()
@blueprint.route('/need-paper-password', methods=['GET','POST'])
def need_papper_password() -> Response:
    """User claims ownership of a paper using submitter provided password."""
    form = PaperPasswordForm()
    if request.method == 'GET':
        return render_template('ownership/need_paper_password.html', **dict(form=form))
    elif request.method == 'POST':
        data=paper_password_post(form, request)
        if data['success']:
            return render_template('ownership/need_paper_password.html', **data)
        else:
            return make_response(render_template('ownership/need_paper_password.html', **data), 400)

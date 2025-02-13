"""arXiv endorsement routes."""

from datetime import datetime, timedelta

# from flask_sqlalchemy import Pagination

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from flask import Blueprint, render_template, Response, request, current_app, abort, redirect, url_for

from arxiv.db.models import EndorsementRequest, Endorsement, TapirUser, Demographic

from .. import get_db

blueprint = Blueprint('endorsement', __name__, url_prefix='/endorsement')


class Pagination:
    def __init__(self, query=None, page=0, per_page=10, total=10000, items=None):
        pass
    pass

@blueprint.route('/request/<int:endorsement_req_id>', methods=['GET'])
def request_detail(endorsement_req_id:int) -> Response:
    """Display a single request for endorsement."""
    session = get_db(current_app).session
    stmt = (select(EndorsementRequest)
            .options(joinedload(EndorsementRequest.endorsee).joinedload(TapirUser.tapir_nicknames),
                     joinedload(EndorsementRequest.endorsement).joinedload(Endorsement.endorser).joinedload(TapirUser.tapir_nicknames),
                     joinedload(EndorsementRequest.audit))
            .filter(EndorsementRequest.request_id == endorsement_req_id)
            )
    endo_req = session.execute(stmt).scalar() or abort(404)
    return render_template('endorsement/request_detail.html',
                           **dict(endorsement_req_id=endorsement_req_id,
                                  endo_req=endo_req,
                                  ))

@blueprint.route('/request/<int:endorsement_req_id>/flip_valid', methods=['POST'])
def flip_valid(endorsement_req_id:int) -> Response:
    """Flip an endorsement_req valid column."""
    session = get_db(current_app).session
    stmt = (select(EndorsementRequest)
            .options(joinedload(EndorsementRequest.endorsement))
            .filter(EndorsementRequest.request_id == endorsement_req_id))
    endo_req = session.execute(stmt).scalar() or abort(404)
    endo_req.endorsement.flag_valid = not bool(endo_req.endorsement.flag_valid)
    session.commit()
    return redirect(url_for('endorsement.request_detail', endorsement_req_id=endorsement_req_id))


@blueprint.route('/request/<int:endorsement_req_id>/flip_score', methods=['POST'])
def flip_score(endorsement_req_id:int) -> Response:
    """Flip an endorsement_req score."""
    session = get_db(current_app).session
    stmt = (select(EndorsementRequest)
            .options(joinedload(EndorsementRequest.endorsement))
            .filter(EndorsementRequest.request_id == endorsement_req_id))
    endo_req = session.execute(stmt).scalar() or abort(404)
    if endo_req.endorsement.point_value > 0:
        endo_req.endorsement.point_value = 0
    else:
        endo_req.endorsement.point_value = 10

    session.commit()
    return redirect(url_for('endorsement.request_detail', endorsement_req_id=endorsement_req_id))


def endorsement_listing(report_type:str, per_page:int, page: int, days_back:int,
                        flagged:bool, not_positive:bool=False):
    """Get data for a list of endorsement requests."""
    session = get_db(current_app).session
    report_stmt = (select(EndorsementRequest)
                   .options(joinedload(EndorsementRequest.endorsee),
                            joinedload(EndorsementRequest.endorsement).joinedload(Endorsement.endorser),)
                   .order_by(EndorsementRequest.request_id.desc())
                   .limit(per_page).offset((page -1) * per_page))
    count_stmt = (select(func.count(EndorsementRequest.request_id)))
    if flagged:
        report_stmt = report_stmt.join(Demographic, EndorsementRequest.endorsee_id == Demographic.user_id)
        report_stmt = report_stmt.filter(Demographic.flag_suspect == 1)
        count_stmt = count_stmt.join(Demographic, EndorsementRequest.endorsee_id == Demographic.user_id)
        count_stmt = count_stmt.filter(Demographic.flag_suspect == 1)

    if not_positive:
        # are joins needed?
        report_stmt = report_stmt.join(Endorsement, EndorsementRequest.request_id == Endorsement.request_id)
        report_stmt = report_stmt.filter(Endorsement.point_value <= 0)
        count_stmt = count_stmt.join(Endorsement, EndorsementRequest.request_id == Endorsement.request_id)
        count_stmt = count_stmt.filter(Endorsement.point_value <= 0)

    if report_type == 'today':
        days_back = 1
    elif not days_back:
        days_back = 7

    window = datetime.now() - timedelta(days=days_back)
    report_stmt = report_stmt.filter(EndorsementRequest.issued_when > window)
    count_stmt = count_stmt.filter(EndorsementRequest.issued_when > window)

    endorsements = session.scalars(report_stmt)
    count = session.execute(count_stmt).scalar_one()
    pagination = Pagination(query=None, page=page, per_page=per_page, total=count, items=None)
    return dict(pagination=pagination, count=count, endorsements=endorsements,
                report_type=report_type, days_back=days_back, not_positive=not_positive)


@blueprint.route('/requests/today', methods=['GET'])
def today() -> Response:
    """Reports todays endorsement requests."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    flagged = args.get('flagged', default=0, type=int)
    _check_report_args(per_page, page, 0, flagged)
    data = endorsement_listing('today', per_page, page, 0, flagged)
    data['title'] = f"Today's {'Flagged ' if flagged else ''}Endorsement Requests"
    return render_template('endorsement/list.html', **data)


@blueprint.route('/requests/last_week', methods=['GET'])
def last_week() -> Response:
    """Reports last 7 days endorsement requests."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    flagged = args.get('flagged', default=0, type=int)
    days_back = args.get('days_back', default=7, type=int)
    _check_report_args(per_page, page, days_back, flagged)
    data = endorsement_listing('last_week', per_page, page, days_back, flagged)
    data['title'] = f"Endorsement {'Flagged ' if flagged else ''}Requests Last {days_back} Days"
    return render_template('endorsement/list.html', **data)


@blueprint.route('/requests/negative', methods=['GET'])
def negative() -> Response:
    """Reports non-positive scored  endorsement requests for last 7 days."""
    args = request.args
    per_page = args.get('per_page', default=12, type=int)
    page = args.get('page', default=1, type=int)
    days_back = args.get('days_back', default=7, type=int)
    _check_report_args(per_page, page, days_back, 0)
    data = endorsement_listing('negative', per_page, page, days_back, False, not_positive=1)
    data['title'] = "Negative Endorsement Requests"
    return render_template('endorsement/list.html', **data)


def _check_report_args(per_page, page, days_back, flagged):
    if per_page > 1000:
        abort(400)
    if page > 10000:
        abort(400)
    if days_back > 365 * 10:
        abort(400)
    if flagged not in [1, 0]:
        abort(400)

import arrow
from flask_jwt_extended import jwt_required
from flask import jsonify, request, Blueprint, current_app

from .dbs.redis import db
from .auth import authorization
from ...utils import decorate

logs = Blueprint('logs', __name__, url_prefix='/logs')


@logs.after_app_request
def save(response):
    now = arrow.utcnow()
    key = 'logs:%s' % request.endpoint
    name = '%s %s %s' % (request.remote_addr, now, response.status_code)
    db.zadd(key, name, now.timestamp)
    return response


@logs.route('/')
@authorization(level=1)
@decorate.arguments('endpoint, start, stop, humanize')
def get(endpoint=None, start:arrow.get=None, stop:arrow.get=None, humanize:int=0):
    """
    ---
    parameters:
      - name: endpoint
        in: query
        type: string
        required: false
        description: route function
        example: logs.get
      - name: start
        in: query
        type: string
        required: false
        description: an ISO formated date or "now"
        example: 2018-05-08 08:20:34.206335 00:00
      - name: stop
        in: query
        type: string
        required: false
        description: an ISO formated date
        example: 2018-05-08 08:20:34.206335 00:00
      - name: humanize
        in: query
        type: integer
        required: false
        description: whether or not time should be human readable
        example: 1
      - name: authorization
        in: header
        type: string
        required: true
        description: an access token
        example: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1MjU3Njg5MDksIm5iZiI6MTUyNTc2ODkwOSwianRpIjoiY2NiNDRhZjEtOThhYi00NTM5LWEyMTAtOGIwNDhjNmNiMDg2IiwiZXhwIjoxNTI1NzY5ODA5LCJpZGVudGl0eSI6InJvb3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.lJ4LjPzPlUQ-DEyXt2qtGtDwD6c3jfeE1eFVVgyZWdE
    """
    if stop in (None, 'now'):
        stop = arrow.utcnow()
    if start is None:
        start = arrow.get(0)
    start = start.timestamp
    stop = stop.timestamp

    logs = {}
    for e in [endpoint] if endpoint else current_app.view_functions:
        data = []
        for result in map(_to_dict, db.zrange('logs:%s' % e, start, stop)):
            if humanize:
                result['time'] = arrow.get(result).humanize
            data.append(result)
        if data:
            logs[e] = data

    return jsonify({'logs': logs})


def _to_dict(x):
    args = x.decode('utf-8').split(' ', 2)
    d = dict(zip(('ip', 'time', 'code'), args))
    d['code'] = int(d['code'])
    return d

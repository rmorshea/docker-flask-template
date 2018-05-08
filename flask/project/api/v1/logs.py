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
@authorization('admin')
@decorate.arguments('endpoint, start, stop, human')
def get(endpoint=None, start:arrow.get=None, stop:arrow.get=None, human:int=0):
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
            if human:
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

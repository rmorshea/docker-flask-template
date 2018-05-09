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
    get logs for application endpoints.
    ---
    parameters:
      - name: endpoint
        in: query
        schema:
            type: string
            example: logs.get
        required: false
        description: route function
      - name: start
        in: query
        schema:
          type: string
          example: 2018-05-08 08:20:34.206335 00:00
        required: false
        description: an ISO formated date or "now"
      - name: stop
        in: query
        schema:
          type: string
          example: 2018-05-08 08:20:34.206335 00:00
        required: false
        description: an ISO formated date
      - name: humanize
        in: query
        schema:
            type: integer
            enum: [0, 1]
            example: 1
        required: false
        description: whether or not time should be human readable
      - name: authorization
        in: header
        schema:
            type: string
            example: Bearer YOUR-TOKEN
        required: true
        description: an access token from a group with level 1 or 0
    definitions:
      EndpointMapping:
        type: object
        properties:
          endpoint:
            type: array
            items:
              $ref: '#/definitions/Log'
      Log:
        type: object
        properties:
          ip:
            type: string
            description: an ip address
            example: 172.18.0.1
          time:
            type: string
            description: iso formated date
            example: 2018-05-08 08:20:34.206335 00:00
          code:
            type: integer
            description: response code for the request
            example: 200
    responses:
      200:
        description: an array or log objects mapped to a corresopnding endpoint function
        schema:
          $ref: '#/definitions/EndpointMapping'
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

    return jsonify(logs)


@logs.record
def setup(app, swagger):
    swagger.definition('Log', log)


def _to_dict(x):
    args = x.decode('utf-8').split(' ', 2)
    d = dict(zip(('ip', 'time', 'code'), args))
    d['code'] = int(d['code'])
    return d

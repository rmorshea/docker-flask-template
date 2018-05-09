import json
from flask import jsonify
from werkzeug.exceptions import HTTPException


def response(http_status_code, **data):
    r = jsonify(data)
    r.status_code = http_status_code
    return r


class Status(HTTPException):
    """Create an http status code"""

    def __init_subclass__(cls, code=None):
        if code is not None:
            cls.code = code

    def __init__(self, reason, **data):
        data['reason'] = reason
        self.data = data
        super().__init__(reason)

    def json(self):
        response = jsonify(self.data)
        response.status_code = self.code
        return response


class Absent(Status, code=400):
    """No result exists."""


class Conflict(Status, code=409):
    """A result with the given specification already exists."""


class Unauthorized(Status, code=401):
    """User does not have access to an endpoint or function."""

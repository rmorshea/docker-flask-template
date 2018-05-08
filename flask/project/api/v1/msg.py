from flask import jsonify
from werkzeug.exceptions import HTTPException


def response(http_status_code, **data):
    return jsonify(data), http_status_code


class Status(HTTPException):
    """Create an http status code"""

    def __init_subclass__(cls, code=None):
        if code is not None:
            cls.code = code

    def __init__(self, reason, **data):
        data['reason'] = reason
        super().__init__(jsonify(data))


class Absent(Status, code=400):
    """No result exists."""


class Conflict(Status, code=400):
    """A result with the given specification already exists."""


class Unauthorized(Status, code=401):
    """User does not have access to an endpoint or function."""

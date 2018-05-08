from flask import jsonify


def response(http_status_code, **data):
    return jsonify(data), http_status_code


class Status(Exception):
    """Create an http status code"""

    def __init_subclass__(cls, code=None):
        if code is not None:
            cls.http_status_code = code
        elif not hasattr(cls, 'http_status_code'):
            raise ValueError('%r has no defined code code' % cls)

    def __init__(self, message):
        self.message = message

    def payload(self):
        return jsonify(self.__dict__)


class Absent(Status, code=400):
    """No result exists."""


class Conflict(Status, code=400):
    """A result with the given specification already exists."""


class Unauthorized(Status, code=401):
    """User does not have access to an endpoint or function."""

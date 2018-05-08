import inspect
from flask import request
from functools import wraps


def arguments(signature):

    parameters = set(map(str.strip, signature.split(',')))

    def setup(function):

        notes = function.__annotations__

        @wraps(function)
        def wrapper(*a, **kw):
            if set(request.args).difference(parameters):
                diff = set(request.args).difference(parameters)
                raise ValueError('Unknown arguments %r.' % list(diff))
            else:
                args = request.args.items()
            kw.update({k: notes[k](v) if k in notes else v for k, v in args})
            return function(*a, **kw)

        return wrapper

    return setup

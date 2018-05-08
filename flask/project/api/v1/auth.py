import os
from functools import wraps

from flask import Blueprint
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from werkzeug.security import check_password_hash

from .msg import Unauthorized
from .dbs.sql.models import User, Group

auth = Blueprint('auth', __name__)


@auth.record
def setup(state):
    state.app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
    jwt = JWTManager(state.app)


def validate(username, password):
    user = User.get(username)
    if user is not None:
        return check_password_hash(user.password, password)
    else:
        return False


def token(username, password, kind='access'):
    if validate(username, password):
        if kind == 'access':
            return create_access_token(identity=username)
        elif kind == 'refresh':
            return create_refresh_token(identity=username)
    else:
        raise Unauthorized('Invalid username or password.')


def authorization(*groups):
    def setup(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            authorize(*groups)
            return function(*args, **kwargs)
        return wrapper
    if not groups:
        raise ValueError('Provide groups or use as decorator')
    if any(map(callable, groups)):
        if len(groups) > 1:
            raise ValueError('To many arguments for decoration.')
        return jwt_required(groups[0])
    else:
        return setup


@jwt_required
def authorize(*groups):
    if None in groups:
        raise ValueError('Root user is always authorized.')
    user = User.current()
    groups = list(_management(groups))
    if user.group not in groups:
        allowed = ', '.join(map(repr, groups))
        form = 'Only %r grouped users are allowed - %r is in the %r group.'
        fill = (allowed, user.username, user.group)
        raise Unauthorized(form % fill)


def _management(groups):
    for g in groups:
        yield g
        yield from Group.management(g)

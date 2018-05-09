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
from .dbs.sql import models

auth = Blueprint('auth', __name__)


@auth.record
def setup(state):
    state.app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
    jwt = JWTManager(state.app)


def validate(username, password):
    user = models.user.User.get(username)
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


def authorization(*groups, level=None, managers=False):
    def setup(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            authorize(*groups, level=level, managers=managers)
            return function(*args, **kwargs)
        return wrapper
    if level is None and any(map(callable, groups)):
        if len(groups) > 1:
            raise ValueError('To many arguments for decoration.')
        return jwt_required(groups[0])
    else:
        return setup


def is_authorized(*groups, level=None, managers=False):
    try:
        authorize(*groups, level=level, managers=managers)
    except Unauthorized:
        return False
    else:
        return True


@jwt_required
def authorize(*groups, level=None, managers=False):
    if managers:
        groups = [models.user.Group.get(g).manager for g in groups]
        groups = list(filter(lambda g : g is not None, groups))
    if None in groups:
        raise Unauthorized('No user can perform this action.')
    user = models.user.User.current()
    if level is not None:
        for relationship in user.groups:
            if relationship.group.level <= level:
                break
        else:
            form = 'The user %r cannot access level %r.'
            raise Unauthorized(form % (user.username, level))
    if groups:
        groups = list(_management(groups))
        for relationship in user.groups:
            if relationship.group.name in groups:
                break
        else:
            allowed = ', '.join(map(repr, groups))
            dissallowed = ', '.join(r.group.name for r in user.groups)
            form = 'Only %r grouped users are allowed - %r is in %r.'
            fill = (allowed, user.username, dissallowed)
            raise Unauthorized(form % fill)
    return True


def _management(groups):
    for g in groups:
        yield g
        yield from models.user.Group.management(g)

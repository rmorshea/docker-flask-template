import os
from functools import wraps

from flask_jwt_extended import (
    jwt_required,
    fresh_jwt_required,
    jwt_refresh_token_required,
    create_access_token,
    create_refresh_token,
)
from werkzeug.security import check_password_hash

from .msg import Unauthorized
from ..dbs.sql import models


def validate_credentials(username, password):
    user = models.user.User.get(username)
    if user is None or not check_password_hash(user.password, password):
        raise Unauthorized('Invalid username or password.')


def tokenize(username, password, fresh=False, refresh=False):
    validate_credentials(username, password)
    access = create_access_token(identity=username, fresh=fresh)
    tokens = {'access': access}
    if refresh:
        tokens['refresh'] = create_refresh_token(identity=username)
    return tokens


def authorization(groups=(), level=None, managers=False):
    def setup(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            authorize(groups, level=level, managers=managers)
            return function(*args, **kwargs)
        return wrapper
    if callable(groups):
        function, groups = groups, []
        return setup(function)
    else:
        return setup


def authorize(groups, level=None, managers=False, kind='access', fresh=False):
    if kind == 'access':
        if fresh:
            auth = _fresh_authorize
        else:
            auth = _stale_authorize
    elif kind == 'refresh':
        auth = _refresh_authorize
    else:
        form = 'Kind must be %r or %r, not %r.'
        fill = ('access', 'refresh', kind)
        raise ValueError(form % fill)
    return auth(groups, level=level, managers=managers)


def _authorize(groups, level=None, managers=False):
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


_stale_authorize = jwt_required(_authorize)
_fresh_authorize = fresh_jwt_required(_authorize)
_refresh_authorize = jwt_refresh_token_required(_authorize)

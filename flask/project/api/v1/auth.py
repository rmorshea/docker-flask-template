import os
from datetime import timedelta
from functools import wraps

from flask import Blueprint, request
from flask_jwt_extended import (
    JWTManager,
    get_jti,
    get_raw_jwt,
    jwt_required,
    create_access_token,
    create_refresh_token,
)
from werkzeug.security import check_password_hash

from .msg import Unauthorized, response
from .dbs.sql import models
from .dbs.redis import db as redis

EXPIRATION = timedelta(minutes=15)

jwt = JWTManager()
auth = Blueprint('auth', __name__)


@auth.record
def setup(state):
    state.app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
    state.app.config['JWT_BLACKLIST_ENABLED'] = True
    state.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = EXPIRATION
    jwt.init_app(state.app)


@jwt.user_loader_callback_loader
def load_user(username):
    return models.user.User.get(username)


@jwt.token_in_blacklist_loader
def token_blacklisted(token):
    state = redis.get('auth.fresh.%s' % token['jti'])
    return not (state is None or bool(int(state)))


@auth.route('/login', methods=['POST'])
def login():
    """
    get a user's access token
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              description: a name for the user
            password:
              type: string
              description: a password for the user
    response:
      '200':
        type: string
        description: an access token
    """
    token = tokenize(request.json['username'], request.json['password'])
    redis.set('auth.fresh.%s' % get_jti(token), 1, EXPIRATION * 1.2)
    return response(201, access=token)


@auth.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    log out a user
    ---
    parameters:
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer <JWT>
        required: true
        description: an access token from a user who can manage the new group
    response:
      '200':
        type: string
        description: an access token
    """
    redis.set('auth.fresh.%s' % get_raw_jwt()['jti'], 0, EXPIRATION * 1.2)
    return response(200, logout=True)


def validate(username, password):
    user = models.user.User.get(username)
    if user is not None:
        return check_password_hash(user.password, password)
    else:
        return False


def tokenize(username, password, kind='access'):
    if validate(username, password):
        if kind == 'access':
            return create_access_token(identity=username)
        elif kind == 'refresh':
            return create_refresh_token(identity=username)
    else:
        raise Unauthorized('Invalid username or password.')


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


def is_authorized(*groups, level=None, managers=False):
    try:
        authorize(*groups, level=level, managers=managers)
    except Unauthorized:
        return False
    else:
        return True


@jwt_required
def authorize(groups, level=None, managers=False):
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

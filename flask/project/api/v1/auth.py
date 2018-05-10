import os
from datetime import timedelta
from functools import wraps

from flask import Blueprint, request
from flask_jwt_extended import JWTManager, get_jti, get_raw_jwt, decode_token
from werkzeug.security import check_password_hash

from .utils.msg import Unauthorized, response
from .utils.creds import authorization, tokenize
from .dbs.sql import models
from .dbs.redis import db as redis

EXPIRATION = timedelta(minutes=15)
BUFFERED_EXPIRATION = EXPIRATION * 1.1

jwt = JWTManager()
auth = Blueprint('auth', __name__, url_prefix='/auth')


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
def is_blacklisted(token):
    return redis.get('auth.tokens.%s' % token['jti']) is None


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
    username = request.json['username']
    password = request.json['password']
    tokens = tokenize(username, password)
    key = 'auth.tokens.%s' % get_jti(tokens['access'])
    redis.set(key, tokens['access'], BUFFERED_EXPIRATION)
    return response(201, **tokens)


@auth.route('/logout', methods=['POST'])
@authorization
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
        description: an access token from the user to log out.
    """
    redis.delete('auth.tokens.%s' % get_raw_jwt()['jti'])
    return response(200, logout=True)


@auth.route('/tokens')
@authorization(level=0)
def tokens():
    """
    get all tokens
    ---
    parameters:
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer <JWT>
        required: true
        description: an access token from the root user
    definitions:
      TokenArray:
        type: object
        properties:
          tokens:
            type: array
            items:
              type: object
              properties:
                token:
                  type: string
                  description: an encoded JWT token
                data:
                  schema:
                    $ref: '#/definitions/TokenData'
      TokenData:
        type: object
        description: the token's decoded data
        properties:
          exp:
            type: integer
            description: expiration time (seconds since epoch UTC)
          fresh:
            type: boolean
            description: whether or not the token is fresh
          iat:
            type: integer
            description: when the token was issued (seconds since epoch UTC)
          identity:
            type: string
            description: username
          jti:
            type: string
            description: unique key for token
          nbf:
            type: integer
            description: toke is invalid until this time (seconds since epoch UTC)
          type:
            type: string
            enum: ["access", "refresh"]
            description: the token type
          user_claims:
            type: object
            description: user claims data
    responses:
      200:
        description: an array containing token data
        schema:
          $ref: '#/definitions/TokenArray'
    """
    result = []
    for key in redis.scan_iter('auth.tokens.*'):
        token = redis.get(key)
        result.append({
            'token': token.decode('utf-8'),
            'data': decode_token(token)
        })
    return response(200, tokens=result)

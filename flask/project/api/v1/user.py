from flask import Blueprint, request, jsonify

from .auth import authorization, authorize, token
from .msg import Conflict, Absent, response
from .dbs.sql import models

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/create', methods=['POST'])
@authorization
def create():
    """
    create a new user
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
            groups:
              type: array
              items:
                type: string
              description: assigns the user to these groups
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer YOUR-TOKEN
        required: true
        description: an access token from a user who can manage the new user
    """
    groups = request.json['groups']
    username = request.json['username']
    password = request.json['password']

    if User.get(username):
        raise Conflict('User already exists.', creation=False)
    else:
        authorize(*groups, managers=True)
        user = User(username=username, password=password)
        models.db.session.add_all(Association(user=user, group=Group.get(g)) for g in groups)
        models.db.session.commit()
        return response(200, creation=True)


@user.route('/delete', methods=['POST'])
@authorization
def delete():
    """
    delete a user
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
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer YOUR-TOKEN
        required: true
        description: an access token from any of the user's managers
    """
    username = request.json['username']

    user = User.get(username)
    if not user:
        raise Absent('User does not exists.', deletion=False)
    else:
        models.db.session.delete(user)
        models.db.session.commit()
        return response(200, deletion=True)


@user.route('/login', methods=['POST'])
def login():
    """
    get an access token
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
        example: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1MjU4MDY5OTYsIm5iZiI6MTUyNTgwNjk5NiwianRpIjoiZjVhNzFlOWItZmQ3Mi00MDUwLWI4NzEtZTZjODQ5OTI0MjM2IiwiZXhwIjoxNTI1ODA3ODk2LCJpZGVudGl0eSI6InJvb3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2YeYsfRW7Mvx8CRt0P8rFlir9Xe1D-ddNMfE0fzjLPk
    """
    return token(request.json['username'], request.json['password'])

from flask import Blueprint, request, jsonify

from .utils.creds import authorization, authorize
from .utils.msg import Conflict, Absent, response
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
          example: Bearer <JWT>
        required: true
        description: an access token from a user who can manage the new user
    """
    groups = request.json['groups']
    username = request.json['username']
    password = request.json['password']

    if User.get(username):
        raise Conflict('User already exists.', creation=False)
    else:
        authorize(groups, managers=True)
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
          example: Bearer <JWT>
        required: true
        description: an access token from any of the user's managers
    """
    username = request.json['username']

    user = User.get(username)
    if not user:
        raise Absent('User does not exists.', deletion=False)
    elif User.current().username != username:
        # authorize user deletion by a manager of that user's group
        authorize([a.group.name for a in user.groups], managers=True)
    models.db.session.delete(user)
    models.db.session.commit()
    return response(200, deletion=True)

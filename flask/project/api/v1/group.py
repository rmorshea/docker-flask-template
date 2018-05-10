from flask import Blueprint, request, jsonify

from .utils.creds import authorization, authorize
from .utils.msg import Conflict, Absent, response
from .dbs.sql import models

group = Blueprint('group', __name__, url_prefix='/group')


@group.route('/create', methods=['POST'])
@authorization
def create():
    """
    create a new user group
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: a name for the group
            level:
              type: integer
              description: the access level of the group (higher number - lower access)
            manager:
              type: string
              description: the name of a group which will manage the new one
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer <JWT>
        required: true
        description: an access token from a user who can manage the new group
    """
    name = request.json['name']
    level = request.json['level']
    manager = request.json['manager']
    if models.user.Group.get(name):
        raise Conflict('Group already exists.', creation=False)
    else:
        authorize(manager, level=level)
        group = models.user.Group(name=name, level=level, manager=manager)
        models.db.session.add(group)
        models.db.session.commit()
        return response(200, creation=True)


@group.route('/delete', methods=['POST'])
@authorization
def delete():
    """
    delete a new user group
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: the name of the group
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer <JWT>
        required: true
        description: an access token from a user who manages the group
    """
    name = request.json['name']
    group = models.user.Group.get(name)
    if not group:
        raise Absent('Group does not exists.', deletion=False)
    else:
        models.db.session.delete(group)
        models.db.session.commit()
        return response(200, deletion=True)

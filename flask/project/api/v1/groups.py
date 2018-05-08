from flask import Blueprint, request, jsonify

from .auth import authorization, authorize, token
from .msg import Conflict, Absent, response
from .dbs.sql.models import db, Group

group = Blueprint('group', __name__, url_prefix='/group')


@group.route('/create', methods=['POST'])
@authorization
def create():
    name = request.json['name']
    manager = request.json['manager']

    if Group.get(name):
        raise Conflict('Group already exists.')
    else:
        authorize(manager)
        group = Group(name=name, manager=manager)
        db.session.add(group)
        db.session.commit()
        return response(200, signup=True)


@group.route('/delete', methods=['POST'])
@authorization
def delete():
    name = request.json['name']

    group = Group.get(name)
    if not group:
        return Absent('Group does not exists.')
    else:
        db.session.delete(group)
        db.session.commit()
        return response(200, deletion=True)

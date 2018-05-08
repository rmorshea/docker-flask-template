from flask import Blueprint, request, jsonify

from .auth import authorization, authorize, token
from .msg import Conflict, Absent, response
from .dbs.sql.models import db, User, Group

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/create', methods=['POST'])
@authorization
def create():
    group = request.json['group']
    username = request.json['username']
    password = request.json['password']

    if User.get(username):
        raise Conflict('User already exists.', creation=False)
    else:
        authorize(Group.get(group).manager)
        user = User(username=username, password=password, group=group)
        db.session.add(user)
        db.session.commit()
        return response(200, creation=True)


@user.route('/delete', methods=['POST'])
@authorization
def delete():
    username = request.json['username']
    password = request.json['password']

    user = User.get(username)
    if not user:
        raise Absent('User does not exists.', deletion=False)
    else:
        db.session.delete(user)
        db.session.commit()
        return response(200, deletion=True)


@user.route('/login', methods=['POST'])
def login():
    return token(request.json['username'], request.json['password'])

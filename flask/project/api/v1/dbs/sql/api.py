import os

from flask import Blueprint

from . import models

sql = Blueprint('sql', __name__)


@sql.record
def setup(state):
    user = os.environ['POSTGRES_USER']
    password = os.environ['POSTGRES_PASSWORD']
    name = os.environ['POSTGRES_DB']
    port = os.environ['POSTGRES_PORT']

    uri = f'postgresql://{user}:{password}@postgres/{name}?port={port}'
    state.app.config['SQLALCHEMY_DATABASE_URI'] = uri
    models.db.init_app(state.app)


@sql.before_app_first_request
def create():
    models.db.create_all()

    models.Group.merge(name='root', manager=None)
    # root user bootstraps other all users and groups into system
    models.User.merge(username='root', password=os.environ['ROOT_USER_PASSWORD'], group='root')

    models.db.session.commit()

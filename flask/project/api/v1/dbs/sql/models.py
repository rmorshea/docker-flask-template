from functools import lru_cache

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import generate_password_hash

from ...msg import Unauthorized

db = SQLAlchemy(session_options={"autoflush": False})


class User(db.Model):

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    _group = db.relationship('Group', back_populates='users')
    group = db.Column(db.String(50), db.ForeignKey('group.name'))

    def __init__(self, **kwargs):
        password = generate_password_hash(kwargs.pop('password'))
        super().__init__(password=password, **kwargs)

    @classmethod
    def get(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def merge(cls, **kwargs):
        new = cls(**kwargs)
        old = cls.get(new.username)
        if not old:
            db.session.merge(new)
            return new
        else:
            return old

    @classmethod
    def current(cls):
        return cls.get(get_jwt_identity())


class Group(db.Model):

    name = db.Column(db.String(50), primary_key=True, nullable=False)
    users = db.relationship('User', back_populates='_group')
    manager = db.Column(db.String(50), db.ForeignKey('group.name'), nullable=True)
    manages = db.relationship('Group')

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def merge(cls, **kwargs):
        new = cls(**kwargs)
        old = cls.get(new.name)
        if not old:
            db.session.add(new)
            return new
        else:
            return old

    @classmethod
    @lru_cache(maxsize=32)
    def management(cls, name):
        return list(cls.iter_management(name))

    @classmethod
    def iter_management(cls, name):
        manager = cls.get(name=name)
        if manager is not None:
            yield manager.name
            yield from cls.iter_management(manager.manager)

from functools import lru_cache

from flask_jwt_extended import get_jwt_identity
from werkzeug.security import generate_password_hash

from ....msg import Unauthorized
from . import db


class Association(db.Model):

    _group = db.Column(db.String(50), db.ForeignKey('group.name'), primary_key=True)
    _user = db.Column(db.String(50), db.ForeignKey('user.username'), primary_key=True)
    group = db.relationship("Group", back_populates="users")
    user = db.relationship("User", back_populates="groups")

    @classmethod
    def get(cls, user, group):
        if isinstance(user, User):
            user = user.username
        if isinstance(group, Group):
            group = group.name
        return cls.query.filter_by(_user=user, _group=group).first()

    @classmethod
    def merge(cls, **kwargs):
        new = cls(**kwargs)
        old = cls.get(new.user, new.group)
        if not old:
            db.session.merge(new)
            return new
        else:
            return old


class User(db.Model):

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    groups = db.relationship("Association", back_populates="user")

    def __init__(self, *args, **kwargs):
        password = generate_password_hash(kwargs.pop('password'))
        super().__init__(*args, password=password, **kwargs)

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
    level = db.Column(db.Integer, nullable=False)
    users = db.relationship("Association", back_populates="group")
    manager = db.Column(db.String(50), db.ForeignKey('group.name'), nullable=True)
    manages = db.relationship('Group')

    def __init__(self, name, manager, level, **kwargs):
        if manager is not None and not level > self.get(manager).level:
            form = 'The manager %r cannot manage a level %s group.'
            raise Unauthorized(form % (manager, level))
        super().__init__(name=name, manager=manager, level=level, **kwargs)

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

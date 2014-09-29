from . import db
from flask.ext.security import (
    UserMixin,
    RoleMixin)
from datetime import datetime


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))


user_groups = db.Table(
    'user_groups',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer(), db.ForeignKey('groups.id')))


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role %r>' % self.name

    def __unicode__(self):
        return self.name


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref(
            'users',
            lazy='dynamic'))
    head_of = db.relationship(
        'Group',
        backref='head',
        lazy='dynamic')
    news = db.relationship(
        'News',
        backref='author',
        lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.email

    def __unicode__(self):
        return self.username


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    where = db.Column(db.String(255))
    when = db.Column(db.String(255))
    short_description = db.Column(db.String(255))
    long_description = db.Column(db.String(700))
    active = db.Column(db.Boolean())
    image = db.Column(db.Boolean())
    users = db.relationship(
        'User',
        secondary=user_groups,
        backref=db.backref('groups',
                           lazy='dynamic'))

    def __repr__(self):
        return '<Group %r>' % self.name

    def __unicode__(self):
        return self.name


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(120))
    body = db.Column(db.String(700))
    pub_date = db.Column(db.DateTime)

    def __init__(self, pub_date=None):
        if pub_date is None:
            pub_date = datetime.utcnow()

    def __repr__(self):
        return '<News %r>' % self.title

    def __unicode__(self):
        return self.title

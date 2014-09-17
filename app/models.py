from . import db
from flask.ext.security import UserMixin, RoleMixin


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
        backref=db.backref('users',
                           lazy='dynamic'))
    head_of = db.relationship(
        'Group',
        backref='head',
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
    short_description = db.Column(db.String(255), unique=True)
    long_description = db.Column(db.String(700), unique=True)
    active = db.Column(db.Boolean())
    users = db.relationship(
        'User',
        secondary=user_groups,
        backref=db.backref('groups',
                           lazy='dynamic'))

    def __repr__(self):
        return '<Group %r>' % self.name

    def __unicode__(self):
        return self.name

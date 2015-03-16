from app import db
from datetime import datetime
import random


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    title = db.Column(db.String(120))
    body = db.Column(db.String(700))
    pub_date = db.Column(db.DateTime())

    def __init__(self, pub_date=None):
        if pub_date is None:
            pub_date = datetime.utcnow()

    def __repr__(self):
        return '<News %r>' % self.title

    def __unicode__(self):
        return self.title


class GroupMetadata(db.Model):
    __tablename__ = 'group_metadata'
    ct_id = db.Column(db.Integer, primary_key=True)
    avatar_id = db.Column(db.String(120))
    description = db.Column(db.String(700))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<GroupMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)


class UserMetadata(db.Model):
    __tablename__ = 'user_metadata'
    ct_id = db.Column(db.Integer, primary_key=True)
    avatar_id = db.Column(db.String(120))
    bio = db.Column(db.String(700))
    twitter = db.Column(db.String(120))
    facebook = db.Column(db.String(120))
    images = db.relationship('Image', backref=db.backref('user'))
    prayer = db.relationship('Prayer', backref=db.backref('user'))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<UserMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)


class Image(db.Model):
    __tablename__ = 'images'
    uuid = db.Column(db.String(120), primary_key=True)
    upload_date = db.Column(db.DateTime())
    upload_to = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user_metadata.ct_id'))

    def __init__(self,
                 uuid,
                 upload_date,
                 upload_to,
                 user_id):
        self.uuid = uuid
        self.upload_date = upload_date
        self.upload_to = upload_to
        self.user_id = user_id

    def __repr__(self):
        return '<Image %r>' % self.uuid

    def __unicode__(self):
        return unicode(self.uuid)


class Prayer(db.Model):
    __tablename__ = 'prayers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_metadata.ct_id'))
    show_user = db.Column(db.Boolean())
    active = db.Column(db.Boolean())
    pub_date = db.Column(db.DateTime())
    body = db.Column(db.String(700))

    def __init__(self,
                 user_id,
                 show_user,
                 active,
                 pub_date,
                 body):
        self.user_id = user_id
        self.show_user = show_user
        self.active = active
        self.pub_date = pub_date
        self.body = body

    def __repr__(self):
        return '<Prayer: user=%r, pub_date=%r>' % (
            self.user_id,
            self.pub_date)


def get_group_metadata(id):
    return GroupMetadata.query.filter_by(ct_id=id).first()


def get_user_metadata(id):
    return UserMetadata.query.filter_by(ct_id=id).first()


def get_random_prayer():
    ''' returns a random still active prayer '''
    prayers = Prayer.query.filter_by(active=True).all()
    if len(prayers) > 0:
        return random.choice(prayers)
    else:
        return None


def get_prayer(id):
    return Prayer.query.get(id)


def get_own_prayers(user_id):
    return Prayer.query.filter_by(
        user_id=user_id).order_by(
            Prayer.pub_date.desc()).all()

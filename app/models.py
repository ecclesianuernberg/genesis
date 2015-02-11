from app import db
from datetime import datetime


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    title = db.Column(db.String(120))
    body = db.Column(db.String(700))
    pub_date = db.Column(db.DateTime())
    image_id = db.Column(db.String(120), db.ForeignKey('images.uuid'))
    image = db.relationship(
        'Image',
        backref=db.backref('news',
                           uselist=False))

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
    image_id = db.Column(db.String(120), db.ForeignKey('images.uuid'))
    image = db.relationship(
        'Image',
        backref=db.backref('group',
                           uselist=False))
    description = db.Column(db.String(700))

    def __init__(self, ct_id=''):
        self.ct_id = ct_id

    def __repr__(self):
        return '<GroupMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)


class UserMetadata(db.Model):
    __tablename__ = 'user_metadata'
    ct_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(120), db.ForeignKey('images.uuid'))
    image = db.relationship(
        'Image',
        backref=db.backref('user_profile',
                           uselist=False))
    bio = db.Column(db.String(700))
    twitter = db.Column(db.String(120))
    facebook = db.Column(db.String(120))

    def __init__(self, ct_id=''):
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
    user = db.Column(db.String(120))

    def __init__(self,
                 uuid='',
                 upload_date='',
                 upload_to='',
                 user=''):
        self.uuid = uuid
        self.upload_date = upload_date
        self.upload_to = upload_to
        self.user = user

    def __repr__(self):
        return '<Image %r>' % self.uuid

    def __unicode__(self):
        return unicode(self.uuid)


class Prayer(db.Model):
    __tablename__ = 'prayers'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120))
    show_user = db.Column(db.Boolean())
    active = db.Column(db.Boolean())
    pub_date = db.Column(db.DateTime())
    body = db.Column(db.String(700))

    def __init__(self,
                 user='',
                 show_user='',
                 active='',
                 pub_date='',
                 body=''):
        self.user = user
        self.show_user = show_user
        self.active = active
        self.pub_date = pub_date
        self.body = body

    def __repr__(self):
        return '<Prayer: user=%r, pub_date=%r>' % (
            self.user,
            self.pub_date)

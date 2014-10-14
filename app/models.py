from . import db
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
    ct_id = db.Column(db.Integer, primary_key=True, unique=True)
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

from . import db
from datetime import datetime


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
    ct_id = db.Column(db.Integer, primary_key=True, unique=True)
    image_id = db.Column(db.String(120), db.ForeignKey('images.uuid'))
    description = db.Column(db.String(700))

    def __init__(self, ct_id=''):
        self.ct_id = ct_id

    def __repr__(self):
        return '<GroupMetadata %r>' % self.ct_id


class Image(db.Model):
    __tablename__ = 'images'
    uuid = db.Column(db.String(120), primary_key=True)
    upload_date = db.Column(db.DateTime())
    uploaded_for = db.Column(db.String(120))
    user = db.Column(db.String(120))
    category_id = db.Column(db.Integer, db.ForeignKey('image_category.id'))
    category = db.relationship(
        'ImageCategory',
        backref=db.backref('images', lazy='dynamic'))

    def __init__(self,
                 uuid='',
                 upload_date='',
                 uploaded_for='',
                 user='',
                 category=''):
        self.uuid = uuid
        self.upload_date = upload_date
        self.uploaded_for = uploaded_for
        self.user = user
        self.category = category

    def __repr__(self):
        return '<Image %r>' % self.uuid

    def __unicode__(self):
        return unicode(self.uuid)


class ImageCategory(db.Model):
    __tablename__ = 'image_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

    def __init__(self, name=''):
        self.name = name

    def __repr__(self):
        return '<ImageCategory %r>' % self.name

    def __unicode__(self):
        return unicode(self.name)

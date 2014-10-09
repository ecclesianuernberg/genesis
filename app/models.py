from . import db
from datetime import datetime


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
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


class GroupMetadata(db.Model):
    __tablename__ = 'group_metadata'
    ct_id = db.Column(db.Integer, primary_key=True, unique=True)
    image = db.Column(db.String(120))
    description = db.Column(db.String(700))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<GroupMetadata %r>' % self.ct_id

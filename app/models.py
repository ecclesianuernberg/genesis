from app import db, ct_connect
from flask import session
from sqlalchemy import func
import random
import datetime


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    title = db.Column(db.String(120))
    body = db.Column(db.String(700))
    pub_date = db.Column(db.DateTime())

    def __init__(self, pub_date=None):
        if pub_date is None:
            pub_date = datetime.datetime.utcnow()

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
    posts = db.relationship('WhatsUp', backref=db.backref('user'))
    comments = db.relationship('WhatsUpComment', backref=db.backref('user'))
    upvotes = db.relationship('WhatsUpUpvote', backref=db.backref('user'))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<UserMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)

    @property
    def ct_data(self):
        ''' returns person data from the churchtools db '''
        return ct_connect.get_person_from_id(self.ct_id)[0]


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


class WhatsUp(db.Model):
    __tablename__ = 'whatsup'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_metadata.ct_id'))
    pub_date = db.Column(db.DateTime())
    active = db.Column(db.DateTime())
    subject = db.Column(db.String(120))
    body = db.Column(db.String(700))
    comments = db.relationship('WhatsUpComment',
                               backref=db.backref('post'),
                               order_by='desc(WhatsUpComment.pub_date)')
    upvotes = db.relationship('WhatsUpUpvote', backref=db.backref('post'))

    def __repr__(self):
        return '<WhatsUp: user=%r, pub_date=%r, subject=%r>' % (
            self.user_id,
            self.pub_date,
            self.subject)

    def did_i_upvote(self):
        active_id = [user['id']
                     for user in session['user']
                     if user['active']][0]

        if active_id in [upvote.user_id for upvote in self.upvotes]:
            return True
        else:
            return False

    def did_i_comment(self):
        active_id = [user['id']
                     for user in session['user']
                     if user['active']][0]

        if active_id in [comment.user_id for comment in self.comments]:
            return True
        else:
            return False


class WhatsUpComment(db.Model):
    __tablename__ = 'whatsup_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('whatsup.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user_metadata.ct_id'))
    pub_date = db.Column(db.DateTime())
    body = db.Column(db.String(700))

    def __init__(self, post_id, user_id, pub_date, body):
        self.post_id = post_id
        self.user_id = user_id
        self.pub_date = pub_date
        self.body = body

    def __repr__(self):
        return '<WhatsUpComment: post=%r, user=%r, pub_date=%r, body=%r>' % (
            self.post_id,
            self.user_id,
            self.pub_date,
            self.body)


class WhatsUpUpvote(db.Model):
    __tablename__ = 'whatsup_upvotes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('whatsup.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user_metadata.ct_id'))

    def __init__(self, post_id, user_id):
        self.post_id = post_id
        self.user_id = user_id

    def __repr__(self):
        return '<WhatsUpUpvote: post=%r, user=%r>' % (
            self.post_id,
            self.user_id)


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


def get_whatsup_post(id):
    return WhatsUp.query.filter_by(id=id).first_or_404()


def get_whatsup_overview():
    ''' returns all posts that are not inactive for the last 60 days and are
    ordered after upvotes made '''
    sixty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=60)

    return WhatsUp.query.outerjoin(
        WhatsUpUpvote).filter(
            WhatsUp.active > sixty_days_ago).group_by(
                WhatsUp.id).order_by(
                    func.count(WhatsUpUpvote.post_id).desc(),
                    WhatsUp.pub_date.desc()).all()


def get_own_whatsup_posts(id):
    return WhatsUp.query.filter_by(
        user_id=id).order_by(
            WhatsUp.pub_date.desc()).all()


def get_latest_whatsup_posts(limit):
    return WhatsUp.query.order_by(
        WhatsUp.pub_date.desc()).limit(
            limit).all()


def get_latest_whatsup_comments(limit):
    return WhatsUpComment.query.order_by(
        WhatsUpComment.pub_date.desc()).limit(
            limit).all()

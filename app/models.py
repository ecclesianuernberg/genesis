from app import APP, DB, ct_connect
from flask import session
from sqlalchemy import func
import flask.ext.whooshalchemy as whooshalchemy
import random
import datetime


class News(DB.Model):
    __tablename__ = 'news'

    id = DB.Column(DB.Integer, primary_key=True)
    author_id = DB.Column(DB.Integer)
    title = DB.Column(DB.String(120))
    body = DB.Column(DB.String(700))
    pub_date = DB.Column(DB.DateTime())

    def __init__(self, pub_date=None):
        if pub_date is None:
            pub_date = datetime.datetime.utcnow()

    def __repr__(self):
        return '<News %r>' % self.title

    def __unicode__(self):
        return self.title


class FrontPage(DB.Model):
    __tablename__ = 'frontpage'

    id = DB.Column(DB.Integer, primary_key=True)

    first_row_image = DB.Column(DB.String(120))
    first_row_link = DB.Column(DB.String(120))

    second_row_image = DB.Column(DB.String(120))
    second_row_link = DB.Column(DB.String(120))

    third_row_left_image = DB.Column(DB.String(120))
    third_row_left_link = DB.Column(DB.String(120))

    third_row_right_image = DB.Column(DB.String(120))
    third_row_right_link = DB.Column(DB.String(120))


class GroupMetadata(DB.Model):
    __tablename__ = 'group_metadata'

    ct_id = DB.Column(DB.Integer, primary_key=True)
    avatar_id = DB.Column(DB.String(120))
    description = DB.Column(DB.String(700))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<GroupMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)

    @property
    def ct_data(self):
        ''' returns group data from the churchtools db '''
        with ct_connect.session_scope() as ct_session:
            return ct_connect.get_group(ct_session, self.ct_id)[0]


class UserMetadata(DB.Model):
    __tablename__ = 'user_metadata'

    ct_id = DB.Column(DB.Integer, primary_key=True)
    avatar_id = DB.Column(DB.String(120))
    bio = DB.Column(DB.String(700))
    twitter = DB.Column(DB.String(120))
    facebook = DB.Column(DB.String(120))
    images = DB.relationship('Image', backref=DB.backref('user'))
    prayer = DB.relationship('Prayer', backref=DB.backref('user'))
    posts = DB.relationship('WhatsUp', backref=DB.backref('user'))
    comments = DB.relationship('WhatsUpComment', backref=DB.backref('user'))
    upvotes = DB.relationship('WhatsUpUpvote', backref=DB.backref('user'))

    def __init__(self, ct_id):
        self.ct_id = ct_id

    def __repr__(self):
        return '<UserMetadata %r>' % self.ct_id

    def __unicode__(self):
        return unicode(self.ct_id)

    def ct_data(self, ct_session):
        ''' returns person data from the churchtools db '''
        return ct_connect.get_person_from_id(ct_session, self.ct_id)[0]


class Image(DB.Model):
    __tablename__ = 'images'

    uuid = DB.Column(DB.String(120), primary_key=True)
    upload_date = DB.Column(DB.DateTime())
    upload_to = DB.Column(DB.String(120))
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user_metadata.ct_id'))

    def __init__(self, uuid, upload_date, upload_to, user_id):
        self.uuid = uuid
        self.upload_date = upload_date
        self.upload_to = upload_to
        self.user_id = user_id

    def __repr__(self):
        return '<Image %r>' % self.uuid

    def __unicode__(self):
        return unicode(self.uuid)


class Prayer(DB.Model):
    __tablename__ = 'prayers'

    id = DB.Column(DB.Integer, primary_key=True)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user_metadata.ct_id'))
    name = DB.Column(DB.String(120))
    active = DB.Column(DB.Boolean())
    pub_date = DB.Column(DB.DateTime())
    body = DB.Column(DB.String(700))

    def __init__(self, user_id, name, active, pub_date, body):
        self.user_id = user_id
        self.name = name
        self.active = active
        self.pub_date = pub_date
        self.body = body

    def __repr__(self):
        return '<Prayer: user=%r, pub_date=%r>' % (self.user_id, self.pub_date)


class WhatsUp(DB.Model):
    __tablename__ = 'whatsup'
    __searchable__ = ['subject', 'body']

    id = DB.Column(DB.Integer, primary_key=True)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user_metadata.ct_id'))
    pub_date = DB.Column(DB.DateTime())
    active = DB.Column(DB.DateTime())
    subject = DB.Column(DB.String(120))
    body = DB.Column(DB.String(700))
    comments = DB.relationship('WhatsUpComment',
                               backref=DB.backref('post'),
                               order_by='desc(WhatsUpComment.pub_date)')
    upvotes = DB.relationship('WhatsUpUpvote', backref=DB.backref('post'))

    def __repr__(self):
        return '<WhatsUp: user=%r, pub_date=%r, subject=%r>' % (self.user_id,
                                                                self.pub_date,
                                                                self.subject)

    def did_i_upvote(self):
        active_id = [user['id'] for user in session['user']
                     if user['active']][0]

        if active_id in [upvote.user_id for upvote in self.upvotes]:
            return True
        else:
            return False

    def did_i_comment(self):
        active_id = [user['id'] for user in session['user']
                     if user['active']][0]

        if active_id in [comment.user_id for comment in self.comments]:
            return True
        else:
            return False


class WhatsUpComment(DB.Model):
    __tablename__ = 'whatsup_comments'
    __searchable__ = ['body']

    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('whatsup.id'))
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user_metadata.ct_id'))
    pub_date = DB.Column(DB.DateTime())
    body = DB.Column(DB.String(700))

    def __init__(self, post_id, user_id, pub_date, body):
        self.post_id = post_id
        self.user_id = user_id
        self.pub_date = pub_date
        self.body = body

    def __repr__(self):
        return '<WhatsUpComment: post=%r, user=%r, pub_date=%r, body=%r>' % (
            self.post_id, self.user_id, self.pub_date, self.body
        )


class WhatsUpUpvote(DB.Model):
    __tablename__ = 'whatsup_upvotes'

    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('whatsup.id'))
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user_metadata.ct_id'))

    def __init__(self, post_id, user_id):
        self.post_id = post_id
        self.user_id = user_id

    def __repr__(self):
        return '<WhatsUpUpvote: post=%r, user=%r>' % (self.post_id,
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
    return Prayer.query.filter_by(user_id=user_id).order_by(
        Prayer.pub_date.desc()).all()


def get_whatsup_post(id):
    return WhatsUp.query.filter_by(id=id).first_or_404()


def get_whatsup_overview():
    ''' returns all posts that are not inactive for the last 60 days and are
    ordered after upvotes made '''
    sixty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=60)

    return WhatsUp.query.outerjoin(WhatsUpUpvote).filter(
        WhatsUp.active > sixty_days_ago).group_by(
            WhatsUp.id).order_by(func.count(WhatsUpUpvote.post_id).desc(),
                                 WhatsUp.pub_date.desc()).all()


def get_own_whatsup_posts(id):
    return WhatsUp.query.filter_by(user_id=id).order_by(
        WhatsUp.pub_date.desc()).all()


def get_latest_whatsup_posts(limit):
    return WhatsUp.query.order_by(WhatsUp.pub_date.desc()).limit(limit).all()


def get_latest_whatsup_comments(limit):
    return WhatsUpComment.query.order_by(
        WhatsUpComment.pub_date.desc()).limit(limit).all()


def search_whatsup_posts(query):
    return WhatsUp.query.whoosh_search(query).all()


def search_whatsup_comments(query):
    return WhatsUpComment.query.whoosh_search(query).all()

# whoosh index stuff
whooshalchemy.whoosh_index(APP, WhatsUp)
whooshalchemy.whoosh_index(APP, WhatsUpComment)

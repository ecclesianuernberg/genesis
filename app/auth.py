from app import app, basic_auth, ct_connect
from flask import abort, g, request, session
from flask.ext.login import UserMixin, current_user
from flask.ext.restful import abort as abort_rest
from functools import wraps
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          SignatureExpired, BadSignature, URLSafeSerializer)
from passlib.hash import bcrypt


class CTUser(UserMixin):
    def __init__(self, uid=None, password=None, active=True):
        self.id = uid
        self.active = active

    def get_user(self):
        try:
            with ct_connect.session_scope() as ct_session:
                user = ct_connect.get_person(ct_session, self.id)

                if user:
                    self.persons = self.get_persons(user)
                    return self
                else:
                    return None

        except:
            return None

    @staticmethod
    def get_persons(user):
        ''' create a dict with all person data that matches
        the logged in email adress. '''
        person_list = []
        for person in user:
            person_list.append({
                'email': person.email,
                'password': person.password,
                'id': person.id,
                'vorname': person.vorname,
                'name': person.name,
                'active': False
            })

        return person_list

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)

        except SignatureExpired:
            # if token is valid but expired
            return None

        except BadSignature:
            # invalid token
            return None

        user = CTUser(uid=data['id'])
        return user.get_user()


def generate_auth_token(user, expiration=600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user['email']})


def get_valid_users(user, password):
    ''' creates a list of valid users from user object and given password '''
    return [person for person in user.persons if person['password']
            if bcrypt.verify(password, person['password'])]


@basic_auth.verify_password
def verify_password(email_or_token, password):
    ''' basic auth used for api '''
    # check if its a token and if its right
    user = CTUser.verify_auth_token(email_or_token)
    valid_user = None

    if not user:
        user_obj = CTUser(uid=email_or_token, password=password)
        user = user_obj.get_user()

        # if it cant even get create a valid_user list it returns a False
        try:
            valid_user = get_valid_users(user, password)
        except:
            return False

        if not valid_user or \
           not user.is_active():
            return False

    # returns first valid user in the list. usually there should be only one.
    # but in a really strange way that its allowed in churchtools that two
    # persons can have the same email adress and password it can run into
    # two or more valid users. for a rest api its not possible to switch
    # between more valid_users. so in this case its always first in list.

    # if user gets authenticated through a token there is now valid_user list
    if not valid_user:
        valid_user = [person for person in user.persons]

    g.user = valid_user[0]

    return True


def own_group(func):
    ''' a decorator that aborts if its not the own group '''

    @wraps(func)
    def decorated_function(*args, **kwargs):
        with ct_connect.session_scope() as ct_session:

            group = ct_connect.get_group(ct_session, kwargs['id'])

            if group is not None:

                heads = ct_connect.get_group_heads(ct_session, kwargs['id'])

                if '/api/' in request.path:
                    is_head = any(head.email == g.user['email']
                                  for head in heads)
                    if not is_head:
                        abort_rest(403)
                else:
                    is_head = any(head.email == current_user.get_id()
                                  for head in heads)
                    if not is_head:
                        abort(403)

            else:
                if '/api/' in request.path:
                    abort_rest(404)
                else:
                    abort(404)

        return func(*args, **kwargs)

    return decorated_function


def prayer_owner(func):
    ''' a decorator that aborts the view if its not the prayer owner '''

    @wraps(func)
    def decorated_function(*args, **kwargs):
        # needs to be done to fix some import problem
        from models import get_prayer

        # getting prayer
        prayer = get_prayer(kwargs['id'])

        # just do this if a prayer with that id exists
        if prayer is not None:

            if '/api/' in request.path:
                if prayer.user_id != g.user['id']:
                    abort_rest(403)
            else:
                if prayer.user_id != [user['id'] for user in session['user']
                                      if user['active']][0]:
                    abort(403)

        # if there is there isnt a prayer abort it with a 404
        else:
            if '/api/' in request.path:
                abort_rest(404)
            else:
                abort(404)

        return func(*args, **kwargs)

    return decorated_function


def own_profile_or_403(user_id):
    ''' allowed to view own profile edit form else abort it '''
    if session['user'][0]['id'] != user_id:
        abort(403)


def active_user():
    ''' return the active user out of user session '''
    return [user for user in session['user'] if user['active']][0]


def generate_feed_auth(user):
    s = URLSafeSerializer(app.config['SECRET_KEY'],
                          salt=app.config['FEED_SALT'])
    return s.dumps({'id': user['email']})


def feed_auth_or_403(token):
    s = URLSafeSerializer(app.config['SECRET_KEY'],
                          salt=app.config['FEED_SALT'])
    try:
        s.loads(token)
    except:
        abort(403)


def is_basic_authorized():
    auth = request.authorization

    if not auth:
        return False

    return verify_password(auth['username'], auth['password'])

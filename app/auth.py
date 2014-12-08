from app import app, basic_auth
from flask import abort, g, request
from flask.ext.login import UserMixin, current_user
from flask.ext.restful import abort as abort_rest
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    SignatureExpired,
    BadSignature)
from passlib.hash import bcrypt
from . import ct_connect


class CTUser(UserMixin):

    def __init__(self, uid=None, password=None, active=True):
        self.id = uid
        self.active = active

    def get_user(self):
        try:
            user = ct_connect.get_person(self.id)
            if user:
                self.username = user.email
                self.password = user.password
                return self
            else:
                return None

        except:
            return None

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

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


@basic_auth.verify_password
def verify_password(email_or_token, password):
    ''' basic auth used for api '''
    # check if its a token and if its right
    user = CTUser.verify_auth_token(email_or_token)

    if not user:
        user_obj = CTUser(uid=email_or_token, password=password)
        user = user_obj.get_user()

        if not user or \
           not bcrypt.verify(password, user.password) or \
           not user.is_active():
            return False

    g.user = user
    return True


def head_of_group_or_403(group_id):
    ''' checks if current_user is head of the group or aborts '''
    heads = ct_connect.get_group_heads(group_id)

    # if the request comes from the api it needs a different way to get the
    # user to check with and a different abort function
    if '/api/' in request.path:
        is_head = any(head.email == g.user.username for head in heads)
        if not is_head:
            abort_rest(403)
    else:
        is_head = any(head.email == current_user.get_id() for head in heads)
        if not is_head:
            abort(403)


def prayer_owner_or_403(prayer_id):
    ''' if user is now the owner of the prayer abort it '''
    # needs to be done to fix some import problem
    from views import get_prayer

    prayer = get_prayer(prayer_id)
    if '/api/' in request.path:
        if prayer.user != g.user.username:
            abort_rest(403)
    else:
        if prayer.user != current_user.get_id():
            abort(403)

from flask.ext.login import UserMixin
from . import ct_connect


class CTUser(UserMixin):

    def __init__(self, uid=None, password=None, active=True):
        self.id = uid
        self.active = active

    def get_user(self, email):
        try:
            user = ct_connect.get_person(email)
            if user:
                self.username = user.email
                self.password = user.password
                return self
            else:
                return None

        except:
            return None

from . import app, db
from flask.ext.login import current_user
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
import models


class MyView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated():
            if current_user.get_id() != 'xsteadfastx@gmail.com':
                return False
            else:
                return True
        else:
            False


admin = Admin(app)
admin.add_view(MyView(models.News, db.session))

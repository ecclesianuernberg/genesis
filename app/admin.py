"""Configure the admin view."""

from flask.ext.login import current_user
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from app import APP, DB, models


class MyView(ModelView):
    """Custom view to manage access."""
    column_display_pk = True
    column_display_all_relations = True

    def is_accessible(self):
        if current_user.is_authenticated():
            if current_user.get_id() != 'xsteadfastx@gmail.com':
                return False
            else:
                return True
        else:
            return False


ADMIN = Admin(APP)
ADMIN.add_view(MyView(models.FrontPage, DB.session))
ADMIN.add_view(MyView(models.News, DB.session))
ADMIN.add_view(MyView(models.GroupMetadata, DB.session))
ADMIN.add_view(MyView(models.UserMetadata, DB.session))
ADMIN.add_view(MyView(models.Image, DB.session))
ADMIN.add_view(MyView(models.Prayer, DB.session))
ADMIN.add_view(MyView(models.WhatsUp, DB.session))
ADMIN.add_view(MyView(models.WhatsUpComment, DB.session))
ADMIN.add_view(MyView(models.WhatsUpUpvote, DB.session))

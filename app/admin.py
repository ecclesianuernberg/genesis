from app import APP, DB
from flask.ext.login import current_user
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
import models


class MyView(ModelView):
    column_display_pk = True
    column_display_all_relations = True

    def is_accessible(self):
        if current_user.is_authenticated():
            if current_user.get_id() != 'xsteadfastx@gmail.com':
                return False
            else:
                return True
        else:
            False


admin = Admin(APP)
admin.add_view(MyView(models.FrontPage, DB.session))
admin.add_view(MyView(models.News, DB.session))
admin.add_view(MyView(models.GroupMetadata, DB.session))
admin.add_view(MyView(models.UserMetadata, DB.session))
admin.add_view(MyView(models.Image, DB.session))
admin.add_view(MyView(models.Prayer, DB.session))
admin.add_view(MyView(models.WhatsUp, DB.session))
admin.add_view(MyView(models.WhatsUpComment, DB.session))
admin.add_view(MyView(models.WhatsUpUpvote, DB.session))

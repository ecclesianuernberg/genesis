from app import app, db
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


admin = Admin(app)
admin.add_view(MyView(models.News, db.session))
admin.add_view(MyView(models.GroupMetadata, db.session))
admin.add_view(MyView(models.UserMetadata, db.session))
admin.add_view(MyView(models.Image, db.session))
admin.add_view(MyView(models.Prayer, db.session))
admin.add_view(MyView(models.WhatsUp, db.session))
admin.add_view(MyView(models.WhatsUpComment, db.session))
admin.add_view(MyView(models.WhatsUpUpvote, db.session))

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user
from flask.ext.security import (
    Security,
    SQLAlchemyUserDatastore)
from flask.ext.migrate import Migrate
from flask_bootstrap import Bootstrap
from flask.ext.misaka import Misaka
import config


app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)

# Bootstrap
Bootstrap(app)

# Misaka Markdown
Misaka(app)

# SQL stuff
db = SQLAlchemy(app)

# Migrate
migrate = Migrate(app, db)

# import
import views
import models


# admin
class SecuredModelView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')


admin = Admin(app)
admin.add_view(SecuredModelView(models.User, db.session))
admin.add_view(SecuredModelView(models.Role, db.session))
admin.add_view(SecuredModelView(models.Group, db.session))

# security
user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

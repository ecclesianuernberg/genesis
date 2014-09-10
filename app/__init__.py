from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.security import Security, SQLAlchemyUserDatastore
import config


app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)

# SQL stuff
db = SQLAlchemy(app)

# import
import views
import models

# admin
admin = Admin(app)
admin.add_view(ModelView(models.User, db.session))

# security
user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

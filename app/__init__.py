from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
import config
app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
db = SQLAlchemy(app)
import views
import models
admin = Admin(app)
admin.add_view(ModelView(models.User, db.session))

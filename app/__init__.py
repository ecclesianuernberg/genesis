from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import LoginManager
import config
app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
import views
import models
admin = Admin(app)
admin.add_view(ModelView(models.User, db.session))

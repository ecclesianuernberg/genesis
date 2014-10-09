from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, current_user
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


# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    return auth.CTUser(uid=userid)


# import
import views
import models
import auth
import admin

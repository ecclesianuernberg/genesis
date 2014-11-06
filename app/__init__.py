from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.migrate import Migrate
from flask_bootstrap import Bootstrap, WebCDN
from flask.ext.misaka import Misaka
from flask.ext.moment import Moment
from flask.ext.pagedown import PageDown
from flask.ext.restful import Api
from flask.ext.httpauth import HTTPBasicAuth
from config import config


app = Flask(__name__)
app.config.from_object(config['development'])

# Bootstrap
Bootstrap(app)
app.extensions['bootstrap']['cdns']['jquery'] = WebCDN(
    '//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/')

# Misaka Markdown
Misaka(app)

# Moment.js
moment = Moment(app)

# SQL stuff
db = SQLAlchemy(app)

# Migrate
migrate = Migrate(app, db)

# PageDown Editor
pagedown = PageDown(app)

# REST API
api = Api(app)

# HTTPAuth
basic_auth = HTTPBasicAuth()

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
import api

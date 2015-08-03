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
from flask_mail import Mail
from config import config
import os

app = Flask(__name__)

# config handling
if os.getenv('FLASK_CONFIG'):
    flask_config = os.getenv('FLASK_CONFIG')
else:
    flask_config = 'default'

app.config.from_object(config[flask_config])

# logging
if not app.debug and not app.testing:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler('/var/log/genesis/genesis.log')
    file_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
                          '[in %(pathname)s:%(lineno)d]'))

    app.logger.addHandler(file_handler)

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

# Mail
mail = Mail(app)

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
    import auth
    return auth.CTUser(uid=userid)

# import
import views
import rest
import feeds
import admin

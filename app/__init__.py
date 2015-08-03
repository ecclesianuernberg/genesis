"""Init Genesis APP."""

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
import os

from config import config


APP = Flask(__name__)

# config handling
if os.getenv('FLASK_CONFIG'):
    FLASK_CONFIG = os.getenv('FLASK_CONFIG')
else:
    FLASK_CONFIG = 'default'

APP.config.from_object(config[FLASK_CONFIG])

# logging
if not APP.debug and not APP.testing:
    import logging
    from logging.handlers import RotatingFileHandler

    FILE_HANDLER = RotatingFileHandler('/var/log/genesis/genesis.log')
    FILE_HANDLER.setLevel(logging.DEBUG)

    FILE_HANDLER.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
                          '[in %(pathname)s:%(lineno)d]'))

    APP.logger.addHandler(FILE_HANDLER)

# Bootstrap
Bootstrap(APP)
APP.extensions['bootstrap']['cdns']['jquery'] = WebCDN(
    '//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/')

# Misaka Markdown
Misaka(APP)

# Moment.js
MOMENT = Moment(APP)

# SQL stuff
DB = SQLAlchemy(APP)

# Migrate
MIGRATE = Migrate(APP, DB)

# PageDown Editor
PAGEDOWN = PageDown(APP)

# Mail
MAIL = Mail(APP)

# REST API
API = Api(APP)

# HTTPAuth
BASIC_AUTH = HTTPBasicAuth()

# Login
LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = 'login'


@LOGIN_MANAGER.user_loader
def load_user(userid):
    """User loader for Genesis."""
    import app.auth
    return app.auth.CTUser(uid=userid)

# import
import app.views
import app.rest
import app.feeds
import app.admin

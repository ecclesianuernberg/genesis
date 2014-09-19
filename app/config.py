import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    NAME = 'G E N E S I S'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    HOST = '127.0.0.1'
    UPLOAD_FOLDER = 'static/group_images'


class DevelopmentConfig(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')

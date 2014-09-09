import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    HOST = '127.0.0.1'


class DevelopmentConfig(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'


class TestingConfig(Config):
    TESTING = True

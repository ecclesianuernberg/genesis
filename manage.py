from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager, Server
import os


# set FLASK_CONFIG environment variable and import app
os.environ['FLASK_CONFIG'] = 'development'
from app import app

server = Server(host=app.config['HOST'])
manager = Manager(app)


@manager.command
def testing():
    ''' Run tests '''
    import pytest
    pytest.main(['-v', '-s'])


manager.add_command('runserver', server)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

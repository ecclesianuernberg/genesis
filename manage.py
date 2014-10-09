from app import app, db
from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager, Server


server = Server(host=app.config['HOST'])
manager = Manager(app)

manager.add_command('runserver', server)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

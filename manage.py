from app import app, db
from flask.ext.script import Manager, Server


server = Server(host=app.config['HOST'])
manager = Manager(app)
manager.add_command('runserver', server)


@manager.command
def create_db():
    db.create_all()


if __name__ == '__main__':
    manager.run()

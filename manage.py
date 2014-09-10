from app import app, db, user_datastore
from flask.ext.script import Manager, Server


server = Server(host=app.config['HOST'])
manager = Manager(app)
manager.add_command('runserver', server)


@manager.command
def create_db():
    ''' creates db'''
    db.create_all()


@manager.command
def create_user(username, password):
    user_datastore.create_user(
        username=username,
        password=password)
    db.session.commit()


if __name__ == '__main__':
    manager.run()

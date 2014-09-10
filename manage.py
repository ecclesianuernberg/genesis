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
def add_admin(username, email, password):
    user = user_datastore.create_user(
        username=username,
        email=email,
        password=password)

    admin_role = user_datastore.find_or_create_role('admin')
    user_datastore.add_role_to_user(user, admin_role)
    db.session.commit()


if __name__ == '__main__':
    manager.run()

from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager, Server
import os
import flask_whooshalchemy

# set FLASK_CONFIG environment variable and import app
os.environ['FLASK_CONFIG'] = 'development'
from app import app, models

server = Server(host=app.config['HOST'])
manager = Manager(app)

manager.add_command('runserver', server)
manager.add_command('db', MigrateCommand)


@manager.command
def whoosh_rebuild():
    'rebuild whoosh index'

    def rebuild_index(model):
        primary_field = model.pure_whoosh.primary_key_name
        searchables = model.__searchable__
        index_writer = flask_whooshalchemy.whoosh_index(app, model)

        entries = model.query.all()

        entry_count = 0
        with index_writer.writer() as writer:
            for entry in entries:
                index_attrs = {}
                for field in searchables:
                    index_attrs[field] = unicode(getattr(entry, field))

                index_attrs[primary_field] = unicode(
                    getattr(entry, primary_field))
                writer.update_document(**index_attrs)
                entry_count += 1

        print 'Rebuilt {0} {1} search index entries.'.format(str(entry_count),
                                                             model.__name__)

    model_list = [models.WhatsUp, models.WhatsUpComment]

    for model in model_list:
        rebuild_index(model)


if __name__ == '__main__':
    manager.run()

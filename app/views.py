from app import app
from flask import render_template
from flask.ext.security import login_required
import models


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/groups')
def groups():
    groups = models.Group.query.filter_by(
        active=True).order_by(models.Group.name).all()
    return render_template('groups.html', groups=groups)


@app.route('/groups/<int:id>')
def group(id):
    group = models.Group.query.filter_by(
        id=id).first()
    return render_template('group.html', group=group)


@app.route('/hello')
@login_required
def hello():
    return 'hello world'

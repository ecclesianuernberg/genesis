from app import app
from flask import render_template
from flask.ext.security import login_required
import models


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/groups')
def groups():
    groups = models.Group.query.all()
    return render_template('groups.html', groups=groups)


@app.route('/hello')
@login_required
def hello():
    return 'hello world'

from app import app
from flask import render_template, redirect, url_for
from flask.ext.security import login_required
import forms
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


@app.route('/groups/<int:id>/edit')
@login_required
def group_edit(id):
    group = models.Group.query.filter_by(
        id=id).first()
    form = forms.EditGroupForm(
        name=group.name,
        short_description=group.short_description,
        long_description=group.long_description,
        active=group.active)
    if form.validate_on_submit():
        return redirect(url_for('group', id=id))
    return render_template(
        'group_edit.html',
        group=group,
        form=form)


@app.route('/hello')
@login_required
def hello():
    return 'hello world'

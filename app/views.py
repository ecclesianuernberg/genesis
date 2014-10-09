from urlparse import urljoin
from passlib.hash import bcrypt
from PIL import Image
from app import app, db
from flask import (
    render_template,
    redirect,
    request,
    url_for)
from flask.ext.login import (
    login_user,
    logout_user,
    login_required,
    current_user)
from . import forms
from . import models
from . import auth
from . import ct_connect
import os.path
import uuid


def make_external(url):
    return urljoin(request.url_root, url)


@app.route('/')
def index():
    return render_template(
        'index.html',
        edit_url=make_external('edit'))


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def index_edit():
    form = forms.EditIndexForm()
    return render_template('index_edit.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user_obj = auth.CTUser(uid=email, password=password)
        user = user_obj.get_user(email)
        if user and bcrypt.verify(
                password, user.password) and user.is_active():
            if login_user(user, remember=True):
                return redirect(url_for('index'))
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/news')
def news():
    pass


@app.route('/groups')
def groups():
    ''' groups overview '''
    groups = ct_connect.get_active_groups()
    return render_template('groups.html', groups=groups)


@app.route('/groups/<int:id>')
def group(id):
    group = ct_connect.get_group(id)
    group_metadata = models.GroupMetadata.query.filter_by(ct_id=id).first()
    group_heads = ct_connect.get_group_heads(id)
    return render_template('group.html',
                           group=group,
                           group_metadata=group_metadata,
                           group_heads=group_heads,
                           edit_url=make_external(
                               '/groups/{}/edit'.format(id)))


def image_resize(in_file, out_file, size=800):
    img = Image.open(in_file)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_file)


@app.route('/groups/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def group_edit(id):
    # if not the head of the group redirect back
    heads = ct_connect.get_group_heads(id)
    is_head = any(head.email == current_user.get_id() for head in heads)

    if not is_head:
        return redirect(url_for('group', id=id))
    else:
        # get group
        group = ct_connect.get_group(id)

        # get metadata
        group_metadata = models.GroupMetadata.query.filter_by(ct_id=id).first()

        # if there is no group_metadata db entry define it
        if not group_metadata:
            group_metadata = models.GroupMetadata(id)
            db.session.add(group_metadata)

        # prefill form with db data
        form = forms.EditGroupForm(
            description=group_metadata.description,
            group_image=group_metadata.image)

        # clicked submit
        if form.validate_on_submit():
            group_metadata.description = form.description.data

            # save image and set the image db true
            form.group_image.data.stream.seek(0)
            try:
                image_uuid = str(uuid.uuid4())
                image_resize(
                    form.group_image.data.stream,
                    os.path.join(
                        app.root_path,
                        app.config['UPLOAD_FOLDER'],
                        image_uuid + '.jpg'),
                    size=800)
                group_metadata.image = image_uuid + '.jpg'
            except:
                pass

            # save to db
            db.session.commit()
            return redirect(url_for('group', id=id))
    return render_template(
        'group_edit.html',
        group=group,
        form=form)

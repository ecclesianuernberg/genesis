from urlparse import urljoin
from PIL import Image
from app import app, db
from flask import (
    render_template,
    redirect,
    request,
    url_for)
from flask.ext.security import (
    login_required,
    roles_accepted,
    current_user)
import forms
import models
import os.path


def make_external(url):
    return urljoin(request.url_root, url)


@app.route('/')
def index():
    return render_template('index.html',
                           edit_url=make_external('edit'))


@app.route('/edit', methods=['GET', 'POST'])
@roles_accepted('admin', 'editor')
def index_edit():
    form = forms.EditIndexForm()
    return render_template('index_edit.html', form=form)


@app.route('/news')
def news():
    pass


@app.route('/groups')
def groups():
    ''' groups overview '''
    groups = models.Group.query.filter_by(
        active=True).order_by(models.Group.name).all()
    return render_template('groups.html', groups=groups)


@app.route('/groups/<int:id>')
def group(id):
    group = models.Group.query.filter_by(
        id=id).first()
    return render_template('group.html',
                           group=group,
                           edit_url=make_external(
                               '/groups/{}/edit'.format(id)))


def image_resize(in_file, out_file, size=800):
    img = Image.open(in_file)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_file)


@app.route('/groups/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def group_edit(id):
    group = models.Group.query.filter_by(
        id=id).first()
    # if not the head of the group redirect back
    if int(current_user.get_id()) != int(group.head_id):
        return redirect(url_for('group', id=id))
    else:
        # prefill form with db data
        form = forms.EditGroupForm(
            name=group.name,
            where=group.where,
            when=group.when,
            short_description=group.short_description,
            long_description=group.long_description,
            active=group.active)

        if form.validate_on_submit():
            group.name = form.name.data
            group.where = form.where.data
            group.when = form.when.data
            group.short_description = form.short_description.data
            group.long_description = form.long_description.data
            group.active = form.active.data

            # save image and set the image db true
            form.group_image.data.stream.seek(0)
            try:
                image_resize(
                    form.group_image.data.stream,
                    os.path.join(
                        app.root_path,
                        app.config['UPLOAD_FOLDER'],
                        str(id) + '.jpg'),
                    size=800)
                group.image = True
            except:
                pass

            # save to db
            db.session.commit()
            return redirect(url_for('group', id=id))
    return render_template(
        'group_edit.html',
        group=group,
        form=form)

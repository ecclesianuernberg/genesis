from app import app, db
from datetime import datetime
from urlparse import urljoin
from passlib.hash import bcrypt
from PIL import Image
from flask import (
    render_template,
    redirect,
    request,
    url_for,
    flash)
from flask.ext.login import (
    login_user,
    logout_user,
    login_required,
    current_user)
from . import (
    forms,
    models,
    auth,
    ct_connect)
import os.path
import uuid
import random


def make_external(url):
    return urljoin(request.url_root, url)


def image_resize(in_file, out_file, size=800):
    img = Image.open(in_file)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_file)


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
        user = user_obj.get_user()
        if user and bcrypt.verify(
                password, user.password) and user.is_active():
            if login_user(user, remember=True):
                flash('Erfolgreich eingeloggt!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Konnte nicht eingeloggt werden!', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Konnte nicht eingeloggt werden!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('Erfolgreich ausgeloggt!', 'success')
    return redirect(url_for('index'))


@app.route('/news')
def news():
    pass


@app.route('/groups')
@login_required
def groups():
    ''' groups overview '''
    groups = ct_connect.get_active_groups()
    return render_template('groups.html', groups=groups)


@app.route('/groups/<int:id>')
def group(id):
    ''' show group '''
    group = ct_connect.get_group(id)
    group_metadata = models.GroupMetadata.query.filter_by(ct_id=id).first()
    group_heads = ct_connect.get_group_heads(id)
    return render_template('group.html',
                           group=group,
                           group_metadata=group_metadata,
                           group_heads=group_heads,
                           edit_url=make_external(
                               '/groups/{}/edit'.format(id)))


@app.route('/groups/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def group_edit(id):
    auth.head_of_group_or_403(id)

    # get group
    group = ct_connect.get_group(id)

    # get metadata
    group_metadata = models.GroupMetadata.query.filter_by(ct_id=id).first()

    # if there is no group_metadata db entry define it
    if not group_metadata:
        group_metadata = models.GroupMetadata(ct_id=id)
        db.session.add(group_metadata)

    # prefill form with db data
    form = forms.EditGroupForm(
        description=group_metadata.description)

    # clicked submit
    if form.validate_on_submit():
        group_metadata.description = form.description.data

        # save image and set the image db true
        form.group_image.data.stream.seek(0)
        try:
            # generate uuid
            image_uuid = str(uuid.uuid4())

            # resize image and save it to upload folder
            image_resize(
                form.group_image.data.stream,
                os.path.join(
                    app.root_path,
                    app.config['UPLOAD_FOLDER'],
                    image_uuid + '.jpg'),
                size=800)

            # generate image db entry
            image = models.Image(
                uuid=image_uuid,
                upload_date=datetime.utcnow(),
                upload_to=request.path,
                user=current_user.get_id())
            db.session.add(image)
            group_metadata.image_id = image_uuid
        except:
            pass

        # save to db
        db.session.commit()
        return redirect(url_for('group', id=id))

    return render_template(
        'group_edit.html',
        group=group,
        form=form)


def get_random_prayer():
    ''' returns a random still active prayer '''
    prayers = models.Prayer.query.filter_by(active=True).all()
    if len(prayers) > 0:
        return random.choice(prayers)
    else:
        return None


def get_prayer(id):
    return models.Prayer.query.get(id)


@app.route('/prayer')
@login_required
def prayer():
    ''' show random prayer '''
    random_prayer = get_random_prayer()
    if random_prayer is not None:
        user = ct_connect.get_person(random_prayer.user)
    else:
        user = None
    return render_template('prayer.html',
                           random_prayer=random_prayer,
                           user=user)


@app.route('/prayer/add', methods=['GET', 'POST'])
@login_required
def prayer_add():
    form = forms.AddPrayerForm(active=True)
    if form.validate_on_submit():
        prayer = models.Prayer(user=current_user.get_id(),
                               show_user=form.show_user.data,
                               active=form.active.data,
                               pub_date=datetime.utcnow(),
                               body=form.body.data)
        db.session.add(prayer)
        db.session.commit()
        flash('Gebetsanliegen abgeschickt!', 'success')
        return redirect(url_for('prayer'))
    return render_template('prayer_add.html', form=form)


@app.route('/prayer/mine')
@login_required
def prayer_mine():
    prayers = models.Prayer.query.filter_by(
        user=current_user.get_id()).order_by(
            models.Prayer.pub_date.desc()).all()
    return render_template('prayer_mine.html', prayers=prayers)


@app.route('/prayer/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def prayer_edit(id):
    auth.prayer_owner_or_403(id)

    prayer = get_prayer(id)
    form = forms.EditPrayerForm(body=prayer.body,
                                show_user=prayer.show_user,
                                active=prayer.active)

    if form.validate_on_submit():
        prayer.body = form.body.data
        prayer.show_user = form.show_user.data
        prayer.active = form.active.data

        db.session.commit()

        flash('Gebetsanliegen veraendert!', 'success')
        return redirect(url_for('prayer_mine'))

    return render_template(
        'prayer_edit.html',
        id=id,
        form=form)


@app.route('/prayer/<int:id>/del')
@login_required
def prayer_del(id):
    auth.prayer_owner_or_403(id)

    prayer = get_prayer(id)

    try:
        db.session.delete(prayer)
        db.session.commit()
        flash('Gebetsanliegen entfernt!', 'success')
        return redirect(url_for('prayer_mine'))
    except:
        flash('Gebetsanliegen konnte nicht entfernt werden!', 'danger')
        return redirect(url_for('prayer_mine'))

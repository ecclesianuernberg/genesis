from app import app, db, forms, models, auth, ct_connect, mailing
from datetime import datetime
from urlparse import urljoin
from PIL import Image, ImageOps
from passlib.hash import bcrypt
from flask import (
    render_template,
    redirect,
    request,
    url_for,
    flash,
    session,
    abort)
from flask.ext.login import (
    login_user,
    logout_user,
    login_required,
    current_user)
import os.path
import uuid
import random


def make_external(url):
    return urljoin(request.url_root, url)


def image_resize(in_file, out_file, size=800):
    img = Image.open(in_file)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_file)


def create_thumbnail(in_file, out_file):
    size = (150, 150)
    img = Image.open(in_file)
    thumb = ImageOps.fit(img, size, Image.ANTIALIAS)
    thumb.save(out_file)


def save_image(image, request_path, user):
    ''' saves image, creates thumbnail and save it to the db '''
    try:
        image_uuid = str(uuid.uuid4())

        # resize image and save it to upload folder
        image_resize(
            image,
            os.path.join(
                app.root_path,
                app.config['UPLOAD_FOLDER'],
                image_uuid + '.jpg'),
            size=800)

        # create thumbnail
        create_thumbnail(
            os.path.join(
                app.root_path,
                app.config['UPLOAD_FOLDER'],
                image_uuid + '.jpg'),
            os.path.join(
                app.root_path,
                app.config['UPLOAD_FOLDER'],
                image_uuid + '-thumb.jpg'))

        # generate image db entry
        image = models.Image(
            uuid=image_uuid,
            upload_date=datetime.utcnow(),
            upload_to=request_path,
            user=user)

        db.session.add(image)
        db.session.commit()

        return image_uuid

    except:
        pass


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
        valid_user = auth.get_valid_users(user, password)

        if valid_user and user.is_active():
            if login_user(user, remember=True):
                # store valid user in session
                session['user'] = valid_user

                # set activate to True on the first user
                session['user'][0]['active'] = True

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


def get_group_metadata(id):
    return models.GroupMetadata.query.filter_by(ct_id=id).first()


@app.route('/groups')
@login_required
def groups():
    ''' groups overview '''
    groups = ct_connect.get_active_groups()
    groups_metadata = [get_group_metadata(i.id) for i in groups]
    return render_template('groups.html',
                           groups=enumerate(groups),
                           groups_metadata=groups_metadata)


@app.route('/group/<int:id>')
def group(id):
    ''' show group '''
    group = ct_connect.get_group(id)
    if not group:
        abort(404)

    group_metadata = get_group_metadata(id)
    group_heads = ct_connect.get_group_heads(id)

    group_edit = False
    if current_user.get_id() in [i.email for i in group_heads]:
        group_edit = True

    return render_template('group.html',
                           group=group,
                           group_metadata=group_metadata,
                           group_heads=group_heads,
                           group_edit=group_edit)


@app.route('/group/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def group_edit(id):
    auth.head_of_group_or_403(id)

    # get group
    group = ct_connect.get_group(id)

    # get metadata
    group_metadata = get_group_metadata(id)

    # if there is no group_metadata db entry define it
    if not group_metadata:
        group_metadata = models.GroupMetadata(ct_id=id)
        db.session.add(group_metadata)

    # prefill form with db data
    form = forms.EditGroupForm(
        description=group_metadata.description,
        where=group.treffpunkt,
        when=group.treffzeit,
        audience=group.zielgruppe)

    # clicked submit
    if form.validate_on_submit():
        try:
            # metadata
            group_metadata.description = form.description.data

            # save image and set the image db true
            form.group_image.data.stream.seek(0)
            group_image = save_image(form.group_image.data.stream,
                                     request_path=request.path,
                                     user=current_user.get_id())
            if group_image:
                group_metadata.image_id = group_image

            # save to metadata db
            db.session.commit()

            # churchtools
            group.treffpunkt = form.where.data
            group.treffzeit = form.when.data
            group.zielgruppe = form.audience.data

            # save data to churchtools db
            ct_connect.SESSION.add(group)
            ct_connect.SESSION.commit()

            flash('Gruppe geaendert!', 'success')
            return redirect(url_for('group', id=id))

        except:
            flash('Fehler aufgetreten!', 'danger')
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
        return redirect(url_for('prayer_mine'))
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


def get_user_metadata(id):
    return models.UserMetadata.query.filter_by(ct_id=id).first()


@app.route('/profile/<int:id>')
@login_required
def profile(id):
    user = ct_connect.get_person_from_id(id)

    if not user:
        abort(404)

    user_metadata = get_user_metadata(id)

    user_edit = False
    for session_user in session['user']:
        if session_user['id'] in [i.id for i in user]:
            user_edit = True
            session_user['active'] = True
        else:
            session_user['active'] = False

    return render_template('profile.html',
                           user=user[0],
                           user_metadata=user_metadata,
                           user_edit=user_edit)


@app.route('/profile/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def profile_edit(id):
    auth.own_profile_or_403(id)

    user = ct_connect.get_person_from_id(id)[0]
    user_metadata = get_user_metadata(id)

    # if there is no user_metadata db entry define it
    if not user_metadata:
        user_metadata = models.UserMetadata(ct_id=id)
        db.session.add(user_metadata)

    # try to prefill form
    form = forms.EditProfileForm(
        street=user.strasse,
        postal_code=user.plz,
        city=user.ort,
        bio=user_metadata.bio,
        twitter=user_metadata.twitter,
        facebook=user_metadata.facebook)

    # clicked submit
    if form.validate_on_submit():
        try:
            # save image and set the image db true
            form.user_image.data.stream.seek(0)

            # metadata
            user_image = save_image(form.user_image.data.stream,
                                    request_path=request.path,
                                    user=current_user.get_id())
            if user_image:
                user_metadata.image_id = user_image

            user_metadata.bio = form.bio.data
            user_metadata.twitter = form.twitter.data
            user_metadata.facebook = form.facebook.data

            # save metadata to metadata db
            db.session.add(user_metadata)
            db.session.commit()

            # churchtools
            user.strasse = form.street.data
            user.plz = form.postal_code.data
            user.ort = form.city.data

            # password
            if form.password.data:
                user.password = bcrypt.encrypt(form.password.data)

            # save data to churchtools db
            ct_connect.SESSION.add(user)
            ct_connect.SESSION.commit()

            flash('Profil geaendert!', 'success')
            return redirect(url_for('profile', id=id))

        except:
            flash('Es ist ein Fehler aufgetreten!', 'danger')
            return redirect(url_for('profile', id=id))

    return render_template(
        'profile_edit.html',
        user=user,
        user_metadata=user_metadata,
        form=form)


def get_recipients(profile_or_group, id):
    if 'profile' in profile_or_group:
        person = ct_connect.get_person_from_id(id)[0]

        return [person.email]

    elif 'group' in profile_or_group:
        group = ct_connect.get_group_heads(id)

        return [i.email for i in group]


@app.route('/mail/<profile_or_group>/<int:id>', methods=['GET', 'POST'])
@login_required
def mail(profile_or_group, id):
    if profile_or_group not in ('profile', 'group'):
        abort(404)

    form = forms.MailForm()

    if form.validate_on_submit():
        try:
            recipients = get_recipients(profile_or_group, id)
            mailing.send_email(sender=current_user.get_id(),
                               recipients=recipients,
                               subject=form.subject.data,
                               body=form.body.data)

            flash('Email gesendet!', 'success')
            return redirect(url_for(profile_or_group, id=id))

        except:
            flash('Es ist ein Fehler aufgetreten!', 'danger')
            return redirect(url_for(profile_or_group, id=id))

    return render_template('mail.html', form=form)

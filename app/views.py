"""All routes for rendered views goes here."""

from urlparse import urljoin
from PIL import Image, ImageOps
from passlib.hash import bcrypt
from unidecode import unidecode
from flask import (render_template, redirect, request, url_for, flash, session,
                   abort, g)
from flask.ext.login import (login_user, logout_user, login_required,
                             current_user)
import os.path
import uuid
import datetime

from app import APP, DB, forms, models, auth, ct_connect, mailing


def make_external(url):
    """Return the external version of a url."""
    return urljoin(request.url_root, url)


def redirect_url(default='index'):
    """Returns a redirect url."""
    return request.referrer or url_for(default)


def image_resize(in_file, out_file, size=800):
    """Resize an image and saves it."""
    img = Image.open(in_file)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_file)


def create_thumbnail(in_file, out_file):
    """Creates a thumbnail."""
    size = (150, 150)
    img = Image.open(in_file)
    thumb = ImageOps.fit(img, size, Image.ANTIALIAS)
    thumb.save(out_file)


def save_image(image, request_path, user_id):
    """Saves image, creates thumbnail and save it to the db."""
    try:
        image_uuid = str(uuid.uuid4())

        # resize image and save it to upload folder
        image_resize(image,
                     os.path.join(APP.root_path, APP.config['UPLOAD_FOLDER'],
                                  image_uuid + '.jpg'),
                     size=800)

        # create thumbnail
        create_thumbnail(os.path.join(APP.root_path,
                                      APP.config['UPLOAD_FOLDER'],
                                      image_uuid + '.jpg'),
                         os.path.join(APP.root_path,
                                      APP.config['UPLOAD_FOLDER'],
                                      image_uuid + '-thumb.jpg'))

        # check if user_metadata exists
        user_metadata = models.get_user_metadata(user_id)

        if not user_metadata:
            metadata = models.UserMetadata(user_id)
            DB.session.add(metadata)

        # generate image db entry
        image = models.Image(uuid=image_uuid,
                             upload_date=datetime.datetime.utcnow(),
                             upload_to=request_path,
                             user_id=user_id)

        DB.session.add(image)
        DB.session.commit()

        return image_uuid

    except:
        return None


def get_recipients(profile_or_group, id):
    """Return recipient list for sending emails."""
    with ct_connect.session_scope() as ct_session:
        if 'profile' in profile_or_group:
            person = ct_connect.get_person_from_id(ct_session, id)[0]

            return [person.email]

        elif 'group' in profile_or_group:
            group = ct_connect.get_group_heads(ct_session, id)

            return [i.email for i in group]


@APP.errorhandler(500)
def internal_error(error):
    """All things that should get done on 500 errors goes here."""
    DB.session.rollback()
    logout_user()

    return redirect(url_for('login'))


@APP.before_request
def before_request():
    """Store search form in g before every request."""
    g.search_form = forms.SearchForm()


@APP.route('/')
@login_required
def index():
    """The frontpage goes here."""
    frontpage = models.FrontPage.query.all()[-1:]

    # if there is at least one frontpage
    if frontpage:
        return render_template('index.html', frontpage=frontpage[-1])
    # else just abort it
    else:
        return render_template('index.html', frontpage=None)


@APP.route('/edit', methods=['GET', 'POST'])
@login_required
@auth.valid_groups_and_users(users=[163], groups=[1])
def index_edit():
    """Frontpage edit form."""
    frontpage = models.FrontPage.query.all()[-1:]

    if not frontpage:
        new_frontpage = models.FrontPage()
        DB.session.add(new_frontpage)

        frontpage = models.FrontPage.query.all()[-1:]

    # prefill form
    form = forms.EditIndexForm(
        first_row_link=frontpage[0].first_row_link,
        second_row_link=frontpage[0].second_row_link,
        third_row_left_link=frontpage[0].third_row_left_link,
        third_row_right_link=frontpage[0].third_row_right_link)

    # on submit
    if form.validate_on_submit():
        try:
            frontpage = models.FrontPage(
                first_row_link=form.first_row_link.data,
                second_row_link=form.second_row_link.data,
                third_row_left_link=form.third_row_left_link.data,
                third_row_right_link=form.third_row_right_link.data)

            # handle uploaded images
            form.first_row_image.data.stream.seek(0)
            image = save_image(image=form.first_row_image.data.stream,
                               request_path=request.path,
                               user_id=auth.active_user()['id'])
            if image:
                frontpage.first_row_image = image

            form.second_row_image.data.stream.seek(0)
            image = save_image(image=form.second_row_image.data.stream,
                               request_path=request.path,
                               user_id=auth.active_user()['id'])
            if image:
                frontpage.second_row_image = image

            form.third_row_left_image.data.stream.seek(0)
            image = save_image(image=form.third_row_left_image.data.stream,
                               request_path=request.path,
                               user_id=auth.active_user()['id'])
            if image:
                frontpage.third_row_left_image = image

            form.third_row_right_image.data.stream.seek(0)
            image = save_image(image=form.third_row_right_image.data.stream,
                               request_path=request.path,
                               user_id=auth.active_user()['id'])
            if image:
                frontpage.third_row_right_image = image

            DB.session.add(frontpage)
            DB.session.commit()

            flash('Index veraendert!', 'success')
            return redirect(url_for('index'))

        except:
            flash('Es ist ein Fehler aufgetreten!', 'danger')
            return redirect(url_for('index_edit'))

    return render_template('index_edit.html', form=form)


@APP.route('/login', methods=['GET', 'POST'])
def login():
    """Login form."""
    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user_obj = auth.CTUser(uid=email, password=password)
        user = user_obj.get_user()

        if user:
            valid_user = auth.get_valid_users(user, password)
        else:
            valid_user = None

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


@APP.route('/logout')
def logout():
    """Route to logout."""
    logout_user()
    flash('Erfolgreich ausgeloggt!', 'success')
    return redirect(url_for('login'))


@APP.route('/news')
def news():
    """Route for the news blog overview."""
    pass


@APP.route('/groups')
@login_required
def groups():
    """Groups overview."""
    with ct_connect.session_scope() as ct_session:
        groups = ct_connect.get_active_groups(ct_session)

        groups_metadata = [models.get_group_metadata(i.id) for i in groups]
        return render_template('groups.html',
                               groups=enumerate(groups),
                               groups_metadata=groups_metadata)


@APP.route('/group/<int:id>', methods=['GET', 'POST'])
@login_required
def group(id):
    """Single group view."""
    with ct_connect.session_scope() as ct_session:
        group = ct_connect.get_group(ct_session, id)
        if not group:
            abort(404)

        group_metadata = models.get_group_metadata(id)
        group_heads = ct_connect.get_group_heads(ct_session, id)

        group_edit = False
        if current_user.get_id() in [i.email for i in group_heads]:
            group_edit = True

        # if someone is trying to make a POST request and group_edit is False
        # abort with a 403 status
        if request.method == 'POST' and group_edit is False:
            abort(403)

        # set form to None that there is something to send to the template
        # if logged in user is not allowed to edit group
        form = None

        if group_edit:
            if not group_metadata:
                group_metadata = models.GroupMetadata(ct_id=id)
                DB.session.add(group_metadata)

            # prefill form with db data
            form = forms.EditGroupForm(description=group_metadata.description,
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
                                             user_id=auth.active_user()['id'])
                    if group_image:
                        group_metadata.avatar_id = group_image

                    # save to metadata db
                    DB.session.commit()

                    # churchtools
                    group.treffpunkt = form.where.data
                    group.treffzeit = form.when.data
                    group.zielgruppe = form.audience.data

                    # save data to churchtools db
                    ct_session.add(group)
                    ct_session.commit()

                    flash('Gruppe geaendert!', 'success')
                    return redirect(url_for('group', id=id))

                except:
                    flash('Fehler aufgetreten!', 'danger')
                    return redirect(url_for('group', id=id))

        return render_template('group.html',
                               group=group,
                               group_metadata=group_metadata,
                               group_heads=group_heads,
                               group_edit=group_edit,
                               form=form,
                               mail_form=forms.MailForm())


@APP.route('/prayer')
@login_required
def prayer():
    """Show random prayer."""
    random_prayer = models.get_random_prayer()

    return render_template('prayer.html', random_prayer=random_prayer)


@APP.route('/prayer/add', methods=['GET', 'POST'])
@login_required
def prayer_add():
    """Add prayer."""
    form = forms.AddPrayerForm(active=True)
    if form.validate_on_submit():
        # check if user_metadata exists
        user_metadata = models.get_user_metadata(auth.active_user()['id'])

        if not user_metadata:
            metadata = models.UserMetadata(auth.active_user()['id'])
            DB.session.add(metadata)
            DB.session.commit()

        prayer = models.Prayer(user_id=auth.active_user()['id'],
                               name=form.name.data,
                               active=form.active.data,
                               pub_date=datetime.datetime.utcnow(),
                               body=form.body.data)

        DB.session.add(prayer)
        DB.session.commit()
        flash('Gebetsanliegen abgeschickt!', 'success')
        return redirect(url_for('prayer_mine'))
    return render_template('prayer_add.html', form=form)


@APP.route('/prayer/mine', methods=['GET', 'POST'])
@login_required
def prayer_mine():
    """Show own prayers."""
    active_user = auth.active_user()

    # getting all own prayers
    prayers = models.get_own_prayers(active_user['id'])

    # creating dict with all forms for own prayers
    edit_forms = {}
    for prayer in prayers:
        edit_forms[prayer.id] = forms.AddPrayerForm(prefix=str(prayer.id),
                                                    body=prayer.body,
                                                    name=prayer.name,
                                                    active=prayer.active)

    if request.method == 'POST':
        try:
            # extract id out of form id
            prayer_id = int(list(request.form)[0].split('-')[0])

            # getting right form out of prayers dict
            edit_prayer_form = edit_forms[prayer_id]

            if edit_prayer_form.validate():
                # getting prayer from id
                prayer = models.get_prayer(prayer_id)

                prayer.body = edit_prayer_form.body.data
                prayer.name = edit_prayer_form.name.data
                prayer.active = edit_prayer_form.active.data

                DB.session.commit()

                flash('Gebetsanliegen veraendert!', 'success')
                return redirect(url_for('prayer_mine'))

        except:
            flash('Es ist ein Fehler aufgetreten!', 'danger')
            return redirect(url_for('prayer_mine'))

    return render_template('prayer_mine.html',
                           prayers=prayers,
                           edit_forms=edit_forms)


@APP.route('/prayer/<int:id>/del')
@login_required
@auth.prayer_owner
def prayer_del(id):
    """Delete prayers."""
    prayer = models.get_prayer(id)

    try:
        DB.session.delete(prayer)
        DB.session.commit()
        flash('Gebetsanliegen entfernt!', 'success')
        return redirect(url_for('prayer_mine'))
    except:
        flash('Gebetsanliegen konnte nicht entfernt werden!', 'danger')
        return redirect(url_for('prayer_mine'))


@APP.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    """User profile."""
    with ct_connect.session_scope() as ct_session:
        user = ct_connect.get_person_from_id(ct_session, id)

        if not user:
            abort(404)

        # geting metadata
        user_metadata = models.get_user_metadata(id)

        # check if user is allowed to edit profile
        user_edit = False
        for session_user in session['user']:
            if session_user['id'] == id:
                user_edit = True
                session_user['active'] = True

            else:
                pass

        # if someone is trying to make a POST request and user_edit is False
        # abort with a 403 status
        if request.method == 'POST' and user_edit is False:
            abort(403)

        # set form to None that there is something to send to the template
        # if logged in user is not allowed to edit profile
        form = None

        # this is for editing users own profile
        if user_edit:
            # set other users in session['user'] inactive
            for session_user in session['user']:
                if session_user['id'] != id:
                    session_user['active'] = False

            # if there is no user_metadata db entry define it
            if not user_metadata:
                user_metadata = models.UserMetadata(ct_id=id)
                DB.session.add(user_metadata)

            # try to prefill form
            form = forms.EditProfileForm(street=user[0].strasse,
                                         postal_code=user[0].plz,
                                         city=user[0].ort,
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
                                            user_id=auth.active_user()['id'])
                    if user_image:
                        user_metadata.avatar_id = user_image

                    user_metadata.bio = form.bio.data
                    user_metadata.twitter = form.twitter.data
                    user_metadata.facebook = form.facebook.data

                    # save metadata to metadata db
                    DB.session.add(user_metadata)
                    DB.session.commit()

                    # churchtools
                    user[0].strasse = form.street.data
                    user[0].plz = form.postal_code.data
                    user[0].ort = form.city.data

                    # password
                    if form.password.data:
                        user[0].password = bcrypt.encrypt(form.password.data)

                    # save data to churchtools db
                    ct_session.add(user[0])
                    ct_session.commit()

                    flash('Profil geaendert!', 'success')
                    return redirect(url_for('profile', id=id))

                except:
                    flash('Es ist ein Fehler aufgetreten!', 'danger')
                    return redirect(url_for('profile', id=id))

        return render_template('profile.html',
                               user=user[0],
                               user_metadata=user_metadata,
                               user_edit=user_edit,
                               form=form,
                               mail_form=forms.MailForm())


@APP.route('/mail/<profile_or_group>/<int:id>', methods=['GET', 'POST'])
@login_required
def mail(profile_or_group, id):
    """Route for sending mails to group leaders or user."""
    if profile_or_group not in ('profile', 'group'):
        abort(404)

    form = forms.MailForm()

    if form.validate_on_submit():
        try:
            # create sender tuple
            active_user = auth.active_user()
            sender = ('{} {}'.format(unidecode(active_user['vorname']),
                                     unidecode(active_user['name'])),
                      active_user['email'])

            recipients = get_recipients(profile_or_group, id)
            mailing.send_email(sender=sender,
                               recipients=recipients,
                               subject=form.subject.data,
                               body=form.body.data)

            flash('Email gesendet!', 'success')
            return redirect(url_for(profile_or_group, id=id))

        except:
            flash('Es ist ein Fehler aufgetreten!', 'danger')
            return redirect(url_for(profile_or_group, id=id))

    return render_template('mail.html', form=form)


@APP.route('/whatsup', methods=['GET', 'POST'])
@login_required
def whatsup_overview():
    """Overview with some metric about how many upvotes a post has."""
    posts = models.get_whatsup_overview()

    form = forms.AddWhatsUp()

    if form.validate_on_submit():
        user_id = auth.active_user()['id']

        # check if user_metadata exists
        user_metadata = models.get_user_metadata(user_id)

        if not user_metadata:
            metadata = models.UserMetadata(user_id)
            DB.session.add(metadata)
            DB.session.commit()

        # create post
        new_post = models.WhatsUp(user_id=user_id,
                                  pub_date=datetime.datetime.utcnow(),
                                  active=datetime.datetime.utcnow(),
                                  subject=form.subject.data,
                                  body=form.body.data)

        DB.session.add(new_post)
        DB.session.commit()

        flash('Post abgeschickt!', 'success')
        return redirect(redirect_url(default='whatsup_overview'))

    # generate a feed auth token
    token = auth.generate_feed_auth(auth.active_user())

    # ct_data needs a DB.session to access the ct database
    with ct_connect.session_scope() as ct_session:
        return render_template('whatsup_overview.html',
                               posts=posts,
                               form=form,
                               ct_session=ct_session,
                               token=token)


@APP.route('/whatsup/new', methods=['GET', 'POST'])
@login_required
def whatsup_overview_new():
    """Ignore all upvotes. Just show newest 20 posts."""
    posts = models.get_latest_whatsup_posts(20)

    form = forms.AddWhatsUp()

    if form.validate_on_submit():
        try:
            user_id = auth.active_user()['id']

            # check if user_metadata exists
            user_metadata = models.get_user_metadata(user_id)

            if not user_metadata:
                metadata = models.UserMetadata(user_id)
                DB.session.add(metadata)
                DB.session.commit()

            # create post
            new_post = models.WhatsUp(user_id=user_id,
                                      pub_date=datetime.datetime.utcnow(),
                                      active=datetime.datetime.utcnow(),
                                      subject=form.subject.data,
                                      body=form.body.data)

            DB.session.add(new_post)
            DB.session.commit()

            flash('Post abgeschickt!', 'success')
            return redirect(redirect_url(default='whatsup_overview_new'))

        except:
            flash('Fehler aufgetreten!', 'danger')
            return redirect(redirect_url(default='whatsup_overview_new'))

    # generate a feed auth token
    token = auth.generate_feed_auth(auth.active_user())

    # ct_data needs a DB.session to access the ct database
    with ct_connect.session_scope() as ct_session:
        return render_template('whatsup_overview_new.html',
                               posts=posts,
                               form=form,
                               ct_session=ct_session,
                               token=token)


@APP.route('/whatsup/<int:id>/upvote')
@login_required
def whatsup_upvote(id):
    """Route to upvote a whatsup post."""
    post = models.get_whatsup_post(id)

    # if already voted just redirect to overview
    if post.did_i_upvote():
        return redirect(redirect_url(default='whatsup_overview'))

    user_id = auth.active_user()['id']

    # check if user_metadata exists
    user_metadata = models.get_user_metadata(user_id)

    if not user_metadata:
        metadata = models.UserMetadata(user_id)
        DB.session.add(metadata)
        DB.session.commit()

    # create upvote
    upvote = models.WhatsUpUpvote(post_id=id, user_id=user_id)

    # set active to now
    post.active = datetime.datetime.utcnow()

    # write to db
    DB.session.add(upvote)
    DB.session.add(post)
    DB.session.commit()

    return redirect(redirect_url(default='whatsup_overview'))


@APP.route('/whatsup/<int:id>', methods=['GET', 'POST'])
@login_required
def whatsup_post(id):
    """Add a whatup post."""
    with ct_connect.session_scope() as ct_session:
        post = models.get_whatsup_post(id)
        form = forms.AddWhatsUpComment()

        if form.validate_on_submit():
            try:
                active_user = auth.active_user()
                user_id = active_user['id']

                # check if user_metadata exists
                user_metadata = models.get_user_metadata(user_id)

                if not user_metadata:
                    metadata = models.UserMetadata(user_id)
                    DB.session.add(metadata)
                    DB.session.commit()

                # add comment
                comment = models.WhatsUpComment(
                    post_id=id,
                    user_id=user_id,
                    pub_date=datetime.datetime.utcnow(),
                    body=form.body.data)

                DB.session.add(comment)
                DB.session.commit()

                # send mail to post owner
                sender = ('{} {}'.format(unidecode(active_user['vorname']),
                                         unidecode(active_user['name'])),
                          active_user['email'])

                recipients = [post.user.ct_data(ct_session).email]

                body = '{} {} hat geschrieben:\n\n{}\n\n{}'.format(
                    unidecode(active_user['vorname']),
                    unidecode(active_user['name']),
                    form.body.data.encode('utf-8'),
                    make_external('/whatsup/{}'.format(id))).decode('utf-8')

                mailing.send_email('Kommentar in "{}"'.format(post.subject),
                                   sender, recipients, body)

                flash('Kommentar abgeschickt!', 'success')
                return redirect(url_for('whatsup_post', id=id))

            except:
                flash('Fehler aufgetreten!', 'danger')
                return redirect(url_for('whatsup_post', id=id))

        return render_template('whatsup_post.html',
                               post=post,
                               form=form,
                               ct_session=ct_session)


@APP.route('/whatsup/mine', methods=['GET', 'POST'])
@login_required
def whatsup_mine():
    """Own whatsup posts."""
    active_user = auth.active_user()

    # getting all own posts
    posts = models.get_own_whatsup_posts(active_user['id'])

    # creating a dict with all edit forms
    edit_forms = {}
    for post in posts:
        edit_forms[post.id] = forms.AddWhatsUp(prefix=str(post.id),
                                               subject=post.subject,
                                               body=post.body)

    if request.method == 'POST':
        # extract id out of form id
        post_id = int(list(request.form)[0].split('-')[0])

        # getting right form out of post form dict
        edit_post_form = edit_forms[post_id]

        if edit_post_form.validate():
            try:
                # getting post
                post = models.get_whatsup_post(post_id)

                # chaning db entry
                post.subject = edit_post_form.subject.data
                post.body = edit_post_form.body.data
                post.active = datetime.datetime.utcnow()

                # save to db
                DB.session.commit()

                flash('Post veraendert!', 'success')
                return redirect(url_for('whatsup_mine'))

            except:
                flash('Es ist ein Fehler aufgetreten!', 'danger')
                return redirect(url_for('post_mine'))

    return render_template('whatsup_mine.html',
                           posts=posts,
                           edit_forms=edit_forms)


@APP.route('/search', methods=['POST'])
@login_required
def search():
    """Search route."""
    if not g.search_form.validate_on_submit():
        return redirect(redirect_url())

    return redirect(url_for('search_results', query=g.search_form.search.data))


@APP.route('/search_results/<query>')
@login_required
def search_results(query):
    """View for search results."""
    with ct_connect.session_scope() as ct_session:
        ct_persons = ct_connect.search_person(ct_session, query)

        persons = [(person, models.get_user_metadata(person.id))
                   for person in ct_persons]

        posts = models.search_whatsup_posts(query)
        comments = models.search_whatsup_comments(query)

        return render_template('search.html',
                               query=query,
                               persons=persons,
                               posts=posts,
                               comments=comments,
                               ct_session=ct_session)

# -*- coding: utf-8 -*-
import os
import app
import flask
import tempfile
import pytest
import feedparser
from app import ct_connect, auth, mailing
from passlib.hash import bcrypt
from PIL import Image
from random import choice
from unidecode import unidecode
from bs4 import BeautifulSoup
from time import sleep
from werkzeug.exceptions import NotFound
from helper import (login, logout, add_prayer, edit_prayer, del_prayer,
                    get_own_group_ids, edit_group, get_other_group_ids,
                    get_wrong_user_id,
                    edit_profile, send_mail, add_whatsup_post,
                    add_whatsup_upvote, add_whatsup_comment, edit_whatsup_post,
                    get_whatsup_feed_posts, get_whatsup_feed_comments,
                    edit_index, search)

# get test user
TEST_USER = app.app.config['TEST_USER']


@pytest.mark.parametrize('test_user', TEST_USER)
def test_login(client, test_user):
    ''' login user'''
    with client as c:
        rv = login(c, test_user['email'], test_user['password'])

        assert rv.status_code == 200
        assert 'Erfolgreich eingeloggt!' in rv.data
        assert flask.session['user'][0]['active'] is True

    # wrong username and password
    rv = login(client, 'foo@bar.com', 'bar')


@pytest.mark.parametrize('test_user', TEST_USER)
def test_logout(client, test_user):
    ''' logout user '''
    rv = logout(client)

    assert rv.status_code == 200
    assert 'Erfolgreich ausgeloggt!' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_index(client, test_user):
    # logged out
    rv = client.get('/')
    assert rv.status_code == 302

    # logged in
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/')
    assert rv.status_code == 200


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_prayer(client, test_user):
    ''' access to random prayer '''
    # not logged in
    rv = client.get('/prayer')

    assert rv.status_code == 302

    # logged in
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/prayer')

    assert rv.status_code == 200


def test_random_prayer(client):
    ''' random prayer view '''
    test_user = TEST_USER[1]
    prayer = 'Dies ist ein Test!'
    name = 'Testname'

    login(client, test_user['email'], test_user['password'])
    add_prayer(client, prayer, name)

    # prayer with show_user
    rv = client.get('/prayer')
    soup = BeautifulSoup(rv.data)

    assert '{}'.format(name) == soup.find_all('div',
                                              class_='panel-heading')[0].text

    # prayer body
    assert prayer in soup.find_all('div', class_='panel-body')[0].text

    # prayer with unabled show_user
    edit_prayer(client, 1, prayer, active=True)
    rv = client.get('/prayer')
    soup = BeautifulSoup(rv.data)

    assert soup.find_all('div', class_='panel-heading')[0].text == ''


@pytest.mark.parametrize('test_user', TEST_USER)
def test_add_prayer(client, test_user):
    ''' adding prayer '''
    login(client, test_user['email'], test_user['password'])

    prayer = 'Test-Anliegen'
    rv = add_prayer(client, prayer, 'Testname')

    assert rv.status_code == 200
    assert 'Gebetsanliegen abgeschickt!' in rv.data
    assert prayer in rv.data

    # check db entry
    db_entry = app.models.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is True
    assert db_entry.name == 'Testname'


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_prayer(client, test_user):
    ''' editing prayer '''
    login(client, test_user['email'], test_user['password'])

    # add prayer
    prayer = 'Test-Anliegen'
    name = 'Testname'
    rv = add_prayer(client, prayer)

    prayer = 'Neues Anliegen'
    rv = edit_prayer(client, 1, prayer, name=name)

    assert rv.status_code == 200
    assert 'Gebetsanliegen veraendert!' in rv.data
    assert prayer in rv.data

    # check db entry
    db_entry = app.models.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is False
    assert db_entry.name == name


def test_del_prayer(client):
    '''delete prayer'''
    test_user = TEST_USER[0]
    login(client, test_user['email'], test_user['password'])

    # add prayer and logout
    add_prayer(client, 'Ein Test zum entfernen')
    logout(client)

    # login as other user and try to delete it
    wrong_test_user = TEST_USER[1]
    login(client, wrong_test_user['email'], wrong_test_user['password'])

    rv = del_prayer(client, 1)

    assert rv.status_code == 403

    logout(client)

    # login as right user again
    login(client, test_user['email'], test_user['password'])
    rv = del_prayer(client, 1)

    assert rv.status_code == 200
    assert 'Gebetsanliegen entfernt!' in rv.data

    # try to delete a prayer which is not existing
    rv = del_prayer(client, 20)

    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_group_list(client, test_user):
    ''' access group list '''
    # not logged in
    rv = client.get('/groups')

    assert rv.status_code == 302

    # logged in
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/groups')

    assert rv.status_code == 200


@pytest.mark.parametrize('test_user', TEST_USER)
def test_group_list(client, test_user):
    ''' group list data '''
    with ct_connect.session_scope() as ct_session:
        group_data = []

        # ct group data
        for group in ct_connect.get_active_groups(ct_session):
            group_data.append(group.bezeichnung.split('-')[-1].encode('utf-8'))
            if group.treffzeit:
                group_data.append(group.treffzeit.encode('utf-8'))
            if group.treffpunkt:
                group_data.append(group.treffpunkt.encode('utf-8'))

        login(client, test_user['email'], test_user['password'])
        rv = client.get('/groups')

        for data in group_data:
            assert data in rv.data

        assert 'avatar-thumb.png' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_group(client, test_user):
    ''' logged out cant access group page'''
    # not logged in
    rv = client.get('/group/1')

    assert rv.status_code == 302

    # logged in
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/group/1')

    assert rv.status_code == 200


@pytest.mark.parametrize('own_group', get_own_group_ids(118))
def test_group_edit_allowed(client, reset_ct_group, own_group, image):
    ''' user can edit groups he is head of '''
    test_user = TEST_USER[0]

    # login
    login(client, test_user['email'], test_user['password'])

    # edit
    rv = edit_group(client, own_group,
                    description='Dies ist ein Test',
                    where='In der Ecclesia',
                    when='Jeden Sonntag',
                    audience='Jeder',
                    image=image)

    # db entry
    avatar_id = app.models.GroupMetadata.query.first().avatar_id

    assert rv.status_code == 200
    assert 'Dies ist ein Test' in rv.data
    assert 'Gruppe geaendert' in rv.data
    assert 'In der Ecclesia' in rv.data
    assert 'Jeden Sonntag' in rv.data
    assert 'Jeder' in rv.data
    assert '{}.jpg'.format(avatar_id) in rv.data

    # check group overview
    rv = client.get('/groups')

    assert '{}-thumb.jpg'.format(avatar_id) in rv.data
    assert 'In der Ecclesia' in rv.data
    assert 'Jeden Sonntag' in rv.data


@pytest.mark.parametrize('not_own_group', get_other_group_ids(118))
def test_group_edit_forbidden(client, not_own_group, image):
    ''' user cant edit groups he isnt head of '''
    test_user = TEST_USER[0]

    # login
    login(client, test_user['email'], test_user['password'])

    # edit
    rv = edit_group(client, not_own_group,
                    description='Dies ist ein Test',
                    where='In der Ecclesia',
                    when='Jeden Sonntag',
                    audience='Jeder',
                    image=image)

    assert rv.status_code == 403


@pytest.mark.parametrize('test_user, allowed',
                         zip(TEST_USER, [True, False, False]))
def test_group_edit_button(client, test_user, allowed):
    ''' edit button on group page '''
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/group/1')
    edit_button = 'edit' in rv.data

    assert edit_button == allowed


@pytest.mark.parametrize('test_user', TEST_USER)
def test_group_data(client, test_user):
    ''' group ct data and metadata on group page '''
    with ct_connect.session_scope() as ct_session:
        groups = ct_connect.get_active_groups(ct_session)
        random_group = choice(groups)

        group_ct_data = ct_connect.get_group(ct_session, random_group.id)

        login(client, test_user['email'], test_user['password'])

        rv = client.get('/group/{}'.format(random_group.id))

        assert group_ct_data.bezeichnung.split(
            '-')[-1].encode('utf-8') in rv.data
        if group_ct_data.treffzeit:
            assert group_ct_data.treffzeit.encode('utf-8') in rv.data
        if group_ct_data.treffpunkt:
            assert group_ct_data.treffpunkt.encode('utf-8') in rv.data


def test_persons():
    ''' creates session dict for persons '''
    with ct_connect.session_scope() as ct_session:
        test_user = app.app.config['TEST_USER'][1]
        user = ct_connect.get_person(ct_session, test_user['email'])
        persons = auth.CTUser.get_persons(user)
        assert persons[0]['email'] == test_user['email']
        assert persons[0]['id'] == test_user['id']
        assert persons[0]['vorname'] == test_user['vorname']
        assert persons[0]['name'] == test_user['name']


@pytest.mark.parametrize('test_user', TEST_USER)
def test_navbar_profile_links(client, test_user):
    ''' profile link in navbar '''
    rv = client.get('/')
    assert '{} {}'.format(test_user['vorname'],
                          test_user['name']) not in rv.data

    # now login
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/')
    assert '{} {}'.format(test_user['vorname'], test_user['name']) in rv.data


def test_navbar_profile_links_same_auth(client, ct_same_username_and_password):
    ''' profile links in navbar for same email password combination '''
    test_user = ct_same_username_and_password[0]

    login(client, test_user['email'], test_user['password'])

    rv = client.get('/')

    for user in ct_same_username_and_password:
        assert '{} {}'.format(user['vorname'], user['name']) in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_valid_users(test_user):
    ''' list of valid users '''
    user = auth.CTUser(uid=test_user['email'],
                       password=test_user['password']).get_user()

    assert auth.get_valid_users(user, test_user['password'])

    # wrong password
    user = auth.CTUser(uid=test_user['email'],
                       password='wrongpassword').get_user()

    assert not auth.get_valid_users(user, 'wrongpassword')


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_profile(client, test_user):
    ''' access profiles '''
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 302

    # now login
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 200
    assert '<h1>{} {}'.format(test_user['vorname'],
                              test_user['name']) in rv.data
    assert 'avatar.png' in rv.data

    # not exisiting profile
    rv = client.get('/profile/7777')
    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile_button(client, test_user):
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/profile/{}'.format(get_wrong_user_id(test_user['id'])))
    assert 'edit' not in rv.data

    rv = client.get('/profile/{}'.format(test_user['id']))
    assert 'edit' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile(client, reset_ct_user, test_user, image):
    ''' edit profile '''
    login(client, test_user['email'], test_user['password'])

    # change profile
    street = 'Teststreet'
    postal_code = '12345'
    city = 'Teststadt'
    bio = 'Testbio'
    password = 'Testpassword'
    twitter = 'http://twitter.com/test'
    facebook = 'http://facebook.com/test'

    rv = edit_profile(client,
                      id=test_user['id'],
                      street=street,
                      postal_code=postal_code,
                      city=city,
                      bio=bio,
                      password=password,
                      twitter=twitter,
                      facebook=facebook,
                      image=image)

    assert rv.status_code == 200
    assert 'Profil geaendert' in rv.data

    # test user_metadata
    user_metadata = app.models.get_user_metadata(test_user['id'])

    assert user_metadata.bio == bio
    assert user_metadata.twitter == twitter
    assert user_metadata.facebook == facebook
    assert user_metadata.avatar_id is not None

    # test profile page
    assert city in rv.data
    assert bio in rv.data
    assert twitter in rv.data
    assert facebook in rv.data
    assert '{}.jpg'.format(user_metadata.avatar_id) in rv.data

    # test churchtools db entries
    with ct_connect.session_scope() as ct_session:
        ct_person = ct_connect.get_person_from_id(ct_session,
                                                  test_user['id'])[0]

        assert ct_person.strasse == street
        assert ct_person.plz == postal_code
        assert ct_person.ort == city

        # check password
        assert bcrypt.verify(password, ct_person.password)

    # now with a user that is not allowed
    wrong_user_id = get_wrong_user_id(test_user['id'])

    rv = edit_profile(client,
                      id=wrong_user_id,
                      street=street,
                      postal_code=postal_code,
                      city=city,
                      bio=bio,
                      password=password,
                      twitter=twitter,
                      facebook=facebook,
                      image=image)

    # not allowed
    assert rv.status_code == 403

    # nothing changed
    rv = client.get('/profile/{}'.format(wrong_user_id))

    assert city not in rv.data
    assert bio not in rv.data
    assert twitter not in rv.data
    assert facebook not in rv.data


def test_profile_session_active_state(client, ct_same_username_and_password):
    ''' active state in session after login and visiting other profiles.
    activate different user in session if the visited profile is allowed to
    use. dont forget the active state on visiting a different users profile.
    '''
    test_user = ct_same_username_and_password

    with client as c:
        login(c, test_user[0]['email'], test_user[0]['password'])

        # first state of active after logged in
        assert flask.session['user'][0]['active'] is True
        assert flask.session['user'][1]['active'] is False

        # go to second user profile
        c.get('/profile/{}'.format(flask.session['user'][1]['id']))

        assert flask.session['user'][0]['active'] is False
        assert flask.session['user'][1]['active'] is True

        # go to a profile that doesnt belong to test user.
        # active state shouldnt have changed
        c.get('/profile/{}'.format(TEST_USER[0]['id']))

        assert flask.session['user'][0]['active'] is False
        assert flask.session['user'][1]['active'] is True


def test_image_resize(image):
    img_out = '{}.jpg'.format(tempfile.mktemp())
    app.views.image_resize(image, img_out, size=800)
    rv = Image.open(img_out)

    assert rv.size == (800, 800)

    # delete outfile
    os.remove(img_out)


def test_create_thumbnail(image):
    img_out = '{}.jpg'.format(tempfile.mktemp())
    app.views.create_thumbnail(image, img_out)
    rv = Image.open(img_out)

    assert rv.size == (150, 150)

    os.remove(img_out)


def test_save_image(client, image):
    test_user = app.app.config['TEST_USER'][1]
    rv = app.views.save_image(image,
                              request_path='test',
                              user_id=test_user['id'])

    # returns a uuid
    assert rv

    # file list with resized image and thumbnail in it
    assert '{}.jpg'.format(rv) \
        and '{}-thumb.jpg'.format(rv) \
        in os.listdir(app.app.config['UPLOAD_FOLDER'])

    # checks db entries
    image = app.models.Image.query.first()

    assert image.user_id == test_user['id']
    assert image.upload_to == 'test'


@pytest.mark.parametrize('test_user, status_code',
                         zip(TEST_USER, [200, 403, 403]))
def test_admin_access_logged_in(client, test_user, status_code):
    login(client, test_user['email'], test_user['password'])

    for view in ['news', 'groupmetadata', 'usermetadata', 'image', 'prayer']:
        rv = client.get('/admin/{}/'.format(view))
        assert rv.status_code == status_code


def test_admin_access_logged_out(client):
    for view in ['news', 'groupmetadata', 'usermetadata', 'image', 'prayer']:
        rv = client.get('/admin/{}/'.format(view))
        assert rv.status_code == 403


def test_mailing():
    ''' mailing functions '''
    sender = TEST_USER[0]['email']
    recipients = [TEST_USER[1]['email']]
    subject = 'Testsubject'
    body = 'Testbody'

    with app.app.app_context():
        with app.mail.record_messages() as outbox:
            mailing.send_email(sender=sender,
                               subject=subject,
                               recipients=recipients,
                               body=body)

            assert outbox[0].sender == sender
            assert outbox[0].recipients == recipients
            assert outbox[0].subject == subject
            assert body in outbox[0].body


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_recipients(test_user):
    # profile
    rv = app.views.get_recipients('profile', test_user['id'])

    assert rv == [test_user['email']]

    # group
    rv = app.views.get_recipients('group', 1)
    assert rv == ['test.leiter@ecclesianuernberg.de', 'xsteadfastx@gmail.com']


@pytest.mark.parametrize('test_user', TEST_USER)
def test_mail_access(client, test_user):
    # access if not logged in
    rv = client.get('/mail/group/1')
    assert rv.status_code == 302
    assert 'You should be redirected automatically' in rv.data

    # a bogus mail url
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/mail/foo/1')
    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_mail(client, test_user):
    ''' sending mail through webform '''
    recipients = [test_user['email']]
    subject = 'Testsubject'
    body = 'Testbody'

    with app.mail.record_messages() as outbox:
        login(client, test_user['email'], test_user['password'])
        rv = send_mail(client, '/mail/profile/{}'.format(test_user['id']),
                       'Testsubject', 'Testbody')

        assert rv.status_code == 200
        assert 'Email gesendet!' in rv.data
        assert outbox[0].sender == '{} {} <{}>'.format(
            unidecode(test_user['vorname'].decode('utf-8')),
            unidecode(test_user['name'].decode('utf-8')), test_user['email'])
        assert outbox[0].recipients == recipients
        assert outbox[0].subject == subject
        assert body in outbox[0].body


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_overview(client, test_user):
    # logged out
    rv = client.get('/whatsup')
    assert rv.status_code == 302

    add_whatsup_post(client, 'subject1', 'body1')

    with pytest.raises(NotFound):
        app.models.get_whatsup_post(1)

    # logged in
    login(client, test_user['email'], test_user['password'])

    # access overview
    rv = client.get('/whatsup')
    assert rv.status_code == 200

    # create post
    rv = add_whatsup_post(client, 'subject1', 'body1')
    assert 'Post abgeschickt!' in rv.data

    # database entries
    rv = app.models.get_whatsup_post(1)
    assert rv.user_id == test_user['id']
    assert rv.subject == 'subject1'
    assert rv.body == 'body1'

    # add some more posts
    sleep(1)
    add_whatsup_post(client, 'subject2', 'body2')
    sleep(1)
    add_whatsup_post(client, 'subject3', 'body3')
    sleep(1)
    add_whatsup_post(client, 'subject4', 'body4')

    # checks if its 4 db entries
    assert len(app.models.WhatsUp.query.all()) == 4

    # checking the order of posts on overview UNVOTED
    rv = client.get('/whatsup')
    soup = BeautifulSoup(rv.data)

    h4s = soup.find_all('h4', class_='media-heading')

    assert 'subject4' in h4s[0].text
    assert 'subject3' in h4s[1].text
    assert 'subject2' in h4s[2].text
    assert 'subject1' in h4s[3].text

    # upvote
    rv = add_whatsup_upvote(client, 1)
    soup = BeautifulSoup(rv.data)

    h4s = soup.find_all('h4', class_='media-heading')

    # subject1 is now first in overview list
    assert 'subject1' in h4s[0].text

    # try to upvote for subject1 again. it should get ignored
    add_whatsup_upvote(client, 1)

    # upvotes entries stayed 1
    assert len(app.models.get_whatsup_post(1).upvotes) == 1


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_overview_new(client, test_user):
    # logged out
    rv = client.get('/whatsup/new')
    assert rv.status_code == 302

    add_whatsup_post(client, 'subject1', 'body1')

    with pytest.raises(NotFound):
        app.models.get_whatsup_post(1)

    # logged in
    login(client, test_user['email'], test_user['password'])

    # access overview
    rv = client.get('/whatsup/new')
    assert rv.status_code == 200

    # create post
    rv = add_whatsup_post(client, 'subject1', 'body1', url='/whatsup/new')
    assert 'Post abgeschickt!' in rv.data

    # database entries
    rv = app.models.get_whatsup_post(1)
    assert rv.user_id == test_user['id']
    assert rv.subject == 'subject1'
    assert rv.body == 'body1'

    # add some more posts
    sleep(1)
    add_whatsup_post(client, 'subject2', 'body2', url='/whatsup/new')
    sleep(1)
    add_whatsup_post(client, 'subject3', 'body3', url='/whatsup/new')
    sleep(1)
    add_whatsup_post(client, 'subject4', 'body4', url='/whatsup/new')

    # checks if its 4 db entries
    assert len(app.models.WhatsUp.query.all()) == 4

    # checking the order of posts on overview UNVOTED
    rv = client.get('/whatsup/new')
    soup = BeautifulSoup(rv.data)

    h4s = soup.find_all('h4', class_='media-heading')

    assert 'subject4' in h4s[0].text
    assert 'subject3' in h4s[1].text
    assert 'subject2' in h4s[2].text
    assert 'subject1' in h4s[3].text

    # upvote
    add_whatsup_upvote(client, 1)
    rv = client.get('/whatsup/new')
    soup = BeautifulSoup(rv.data)

    h4s = soup.find_all('h4', class_='media-heading')

    # subject4 is still first in overview list
    assert 'subject4' in h4s[0].text

    # try to upvote for subject1 again. it should get ignored
    add_whatsup_upvote(client, 1)

    # upvotes entries stayed 1
    assert len(app.models.get_whatsup_post(1).upvotes) == 1


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_post(client, test_user):
    with app.app.app_context():
        with app.mail.record_messages() as outbox:
            # add post
            login(client, test_user['email'], test_user['password'])
            add_whatsup_post(client, 'subject', 'body')

            # logout and try to access it
            logout(client)
            rv = client.get('/whatsup/1')

            assert rv.status_code == 302

            # login again
            login(client, test_user['email'], test_user['password'])

            # add comment
            rv = add_whatsup_comment(client, 1, 'cömment1')

            assert rv.status_code == 200
            assert 'Kommentar abgeschickt!' in rv.data

            # database entries
            rv = app.models.get_whatsup_post(1)

            assert rv.comments[0].body == 'cömment1'.decode('utf-8')
            assert rv.comments[0].post_id == 1
            assert rv.comments[0].user_id == test_user['id']

            # add 3 more comments
            sleep(1)
            add_whatsup_comment(client, 1, 'comment2')
            sleep(1)
            add_whatsup_comment(client, 1, 'comment3')
            sleep(1)
            add_whatsup_comment(client, 1, 'comment4')

            assert len(app.models.get_whatsup_post(1).comments) == 4

            # create soup
            rv = client.get('/whatsup/1')
            soup = BeautifulSoup(rv.data)

            rv = soup.find_all('div', class_='media-body')

            # discussion icon counter
            assert '4' in rv[0].text

            # checking comment order
            assert 'comment4' in rv[1].text
            assert 'comment3' in rv[2].text
            assert 'comment2' in rv[3].text
            assert 'cömment1'.decode('utf-8') in rv[4].text

            # checking names
            assert '{} {}'.format(
                test_user['vorname'],
                test_user['name']) in rv[0].text.encode('utf-8')
            assert '{} {}'.format(
                test_user['vorname'],
                test_user['name']) in rv[1].text.encode('utf-8')
            assert '{} {}'.format(
                test_user['vorname'],
                test_user['name']) in rv[2].text.encode('utf-8')
            assert '{} {}'.format(
                test_user['vorname'],
                test_user['name']) in rv[3].text.encode('utf-8')
            assert '{} {}'.format(
                test_user['vorname'],
                test_user['name']) in rv[4].text.encode('utf-8')

            # check notification emails
            assert outbox[0].sender == '{} {} <{}>'.format(
                unidecode(test_user['vorname'].decode('utf-8')), unidecode(
                    test_user['name'].decode('utf-8')), test_user['email'])
            assert outbox[0].subject == 'Kommentar in "{}"'.format('subject')
            assert '{} {} hat geschrieben:'.format(
                unidecode(test_user['vorname'].decode('utf-8')),
                unidecode(test_user['name'].decode('utf-8'))) in outbox[0].body
            assert 'cömment1'.decode('utf-8') in outbox[0].body
            assert '/whatsup/1' in outbox[0].body


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_mine(client, test_user):
    # logged out
    rv = client.get('/whatsup/mine')

    assert rv.status_code == 302

    # log in
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/whatsup/mine')

    assert rv.status_code == 200

    # add posts
    add_whatsup_post(client, 'subject1', 'body1')
    sleep(1)
    add_whatsup_post(client, 'subject2', 'body2')

    rv = client.get('/whatsup/mine')
    soup = BeautifulSoup(rv.data)

    rv = soup.find_all('div', class_='panel-body')

    # order of own posts
    assert 'body2' in rv[0].text
    assert 'body1' in rv[1].text

    rv = edit_whatsup_post(client, 2, 'newsubject2', 'newbody2')

    # check flash message
    assert 'Post veraendert!' in rv.data

    soup = BeautifulSoup(rv.data)
    rv = soup.find_all('div', class_='panel-body')

    # changed body
    assert 'newbody2' in rv[0].text

    # changed subject
    rv = soup.find_all('h4')

    assert 'newsubject2' in rv[0].text


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_feed_posts(client, test_user):
    # prepare everything
    login(client, test_user['email'], test_user['password'])
    add_whatsup_post(client, 'subject1', 'body1')
    sleep(1)
    add_whatsup_post(client, 'subject2', 'body2')
    logout(client)

    # logged out
    rv = client.get('/feeds/whatsup.atom')

    # not allowed
    assert rv.status_code == 403

    # logged in
    token = auth.generate_feed_auth(test_user)
    rv = get_whatsup_feed_posts(client, token)

    assert rv.status_code == 200

    # parse feed
    rv = feedparser.parse(rv.data)

    assert rv['feed']['title'] == 'Recent WhatsUp Posts'
    assert rv.entries[0].title == 'subject2'
    assert rv.entries[1].title == 'subject1'
    assert rv.entries[0].content[0]['value'] == 'body2'
    assert rv.entries[1].content[0]['value'] == 'body1'
    assert rv.entries[0].author == '{} {}'.format(
        unidecode(test_user['vorname'].decode('utf-8')),
        unidecode(test_user['name'].decode('utf-8')))
    assert rv.entries[1].author == '{} {}'.format(
        unidecode(test_user['vorname'].decode('utf-8')),
        unidecode(test_user['name'].decode('utf-8')))

    # wrong token
    token = 'foobar'
    rv = get_whatsup_feed_posts(client, token)

    assert rv.status_code == 403


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_feed_comments(client, test_user):
    # prepare everything
    login(client, test_user['email'], test_user['password'])
    add_whatsup_post(client, 'subject1', 'body1')
    sleep(1)
    add_whatsup_comment(client, 1, 'comment1')
    sleep(1)
    add_whatsup_comment(client, 1, 'comment2')
    logout(client)

    # logged out
    rv = client.get('/feeds/whatsup-comments.atom')

    # not allowed
    assert rv.status_code == 403

    # logged in
    token = auth.generate_feed_auth(test_user)
    rv = get_whatsup_feed_comments(client, token)

    assert rv.status_code == 200

    # parse feed
    rv = feedparser.parse(rv.data)

    assert rv['feed']['title'] == 'Recent WhatsUp Comments'
    assert rv.entries[0].title == 'Kommentar fuer "subject1" von {} {}'.format(
        unidecode(test_user['vorname'].decode('utf-8')),
        unidecode(test_user['name'].decode('utf-8')))
    assert rv.entries[0].content[0]['value'] == 'comment2'
    assert rv.entries[1].content[0]['value'] == 'comment1'
    assert rv.entries[0].author == '{} {}'.format(
        unidecode(test_user['vorname'].decode('utf-8')),
        unidecode(test_user['name'].decode('utf-8')))
    assert rv.entries[1].author == '{} {}'.format(
        unidecode(test_user['vorname'].decode('utf-8')),
        unidecode(test_user['name'].decode('utf-8')))

    # wrong token
    token = 'foobar'
    rv = get_whatsup_feed_comments(client, token)

    assert rv.status_code == 403


@pytest.mark.parametrize('test_user', TEST_USER)
def test_whatsup_feed_links(test_user, client):
    # prepare everything
    login(client, test_user['email'], test_user['password'])
    token = auth.generate_feed_auth(test_user)

    # overview
    rv = client.get('/whatsup')

    soup = BeautifulSoup(rv.data)
    feed_links = [i['href'] for i in soup.find_all('link')
                  if 'feed' in i['href']]

    assert len(feed_links) == 2
    assert feed_links[0] == '/feeds/whatsup.atom?token={}'.format(token)
    assert feed_links[1] == '/feeds/whatsup-comments.atom?token={}'.format(
        token)

    # new
    rv = client.get('/whatsup/new')

    soup = BeautifulSoup(rv.data)
    feed_links = [i['href'] for i in soup.find_all('link')
                  if 'feed' in i['href']]

    assert len(feed_links) == 2
    assert feed_links[0] == '/feeds/whatsup.atom?token={}'.format(token)
    assert feed_links[1] == '/feeds/whatsup-comments.atom?token={}'.format(
        token)


def test_edit_index(client, image):
    # logged out
    rv = client.get('/edit')

    assert rv.status_code == 302

    # wrong user
    test_user = TEST_USER[1]
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/edit')

    assert rv.status_code == 405

    logout(client)

    # right user
    test_user = TEST_USER[0]
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/edit')

    assert rv.status_code == 200

    rv = edit_index(client, image, 'http://eins.com', 'http://zwei.com',
                    'http://drei.com', 'http://vier.com')

    # check db
    rv = app.models.FrontPage.query.all()[-1]

    assert rv.first_row_image is not None
    assert rv.first_row_link == 'http://eins.com'
    assert rv.second_row_image is not None
    assert rv.second_row_link == 'http://zwei.com'
    assert rv.third_row_left_image is not None
    assert rv.third_row_left_link == 'http://drei.com'
    assert rv.third_row_right_image is not None
    assert rv.third_row_right_link == 'http://vier.com'

    # check rendered page
    first_row_image = rv.first_row_image
    second_row_image = rv.second_row_image
    third_row_left_image = rv.third_row_left_image
    third_row_right_image = rv.third_row_right_image

    rv = client.get('/')

    assert 'http://eins.com' in rv.data
    assert '{}.jpg'.format(first_row_image) in rv.data
    assert 'http://zwei.com' in rv.data
    assert '{}.jpg'.format(second_row_image) in rv.data
    assert 'http://drei.com' in rv.data
    assert '{}.jpg'.format(third_row_left_image) in rv.data
    assert 'http://vier.com' in rv.data
    assert '{}.jpg'.format(third_row_right_image) in rv.data


def test_search_person():
    with ct_connect.session_scope() as session:
        # one word without capitalization
        name = TEST_USER[1]['vorname'].lower()
        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[1]['id'] in rv
        assert TEST_USER[2]['id'] in rv

        # one word with capitalization
        name = TEST_USER[1]['vorname'].capitalize()
        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[1]['id'] in rv
        assert TEST_USER[2]['id'] in rv

        # one word full capitalized
        name = TEST_USER[1]['vorname'].upper()
        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[1]['id'] in rv
        assert TEST_USER[2]['id'] in rv

        # two words without capitalization
        name = '{} {}'.format(TEST_USER[0]['vorname'].lower(),
                              TEST_USER[0]['name'].lower())
        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[0]['id'] in rv

        # two words with capitalization
        name = '{} {}'.format(TEST_USER[0]['vorname'].capitalize(),
                              TEST_USER[0]['name'].capitalize())

        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[0]['id'] in rv

        # two words full capitalization
        name = '{} {}'.format(TEST_USER[0]['vorname'].upper(),
                              TEST_USER[0]['name'].upper())

        rv = [i.id for i in ct_connect.search_person(session, name)]

        assert TEST_USER[0]['id'] in rv


def test_search_whatsup(client):
    test_user = TEST_USER[0]
    login(client, test_user['email'], test_user['password'])

    # add whatsup posts
    add_whatsup_post(client, 'erstes subject', 'erster body')
    sleep(1)
    add_whatsup_post(client, 'zweites subject', 'zweiter body')
    sleep(1)
    add_whatsup_post(client, 'drittes subject', 'dritter body')
    sleep(1)

    # add comment
    add_whatsup_comment(client, 1, 'erster kommentar')
    add_whatsup_comment(client, 1, 'zweiter kommentar')

    # search for erstes subject
    rv = app.models.search_whatsup_posts('erstes')

    assert len(rv) == 1
    assert rv[0].subject == 'erstes subject'
    assert rv[0].body == 'erster body'

    rv = app.models.search_whatsup_posts('erstes subject')

    assert len(rv) == 1
    assert rv[0].subject == 'erstes subject'
    assert rv[0].body == 'erster body'

    # search for erster body
    rv = app.models.search_whatsup_posts('erster body')

    assert len(rv) == 1
    assert rv[0].subject == 'erstes subject'
    assert rv[0].body == 'erster body'

    # search for the word subject
    rv = [i.subject for i in app.models.search_whatsup_posts('subject')]

    assert len(rv) == 3
    assert 'erstes subject' in rv
    assert 'zweites subject' in rv
    assert 'drittes subject' in rv

    # search for the word body
    rv = [i.subject for i in app.models.search_whatsup_posts('body')]

    assert len(rv) == 3
    assert 'erstes subject' in rv
    assert 'zweites subject' in rv
    assert 'drittes subject' in rv

    # search for comment
    rv = app.models.search_whatsup_comments('erster')

    assert len(rv) == 1
    assert rv[0].body == 'erster kommentar'


@pytest.mark.parametrize('test_user', TEST_USER)
def test_search_view(client, test_user):
    login(client, test_user['email'], test_user['password'])

    # add whatsup posts
    add_whatsup_post(client, 'erstes subject', 'erster body')
    sleep(1)
    add_whatsup_post(client, 'zweites subject', 'zweiter body')
    sleep(1)
    add_whatsup_post(client, 'drittes subject', 'dritter body')
    sleep(1)

    # add comment
    add_whatsup_comment(client, 1, 'erster kommentar')
    add_whatsup_comment(client, 1, 'zweiter kommentar')

    # search for person
    person = TEST_USER[0]

    rv = search(client, 'marvin')
    soup = BeautifulSoup(rv.data)

    assert 'marvin' in soup.find_all('h1')[0].text
    assert 'Personen' in soup.find_all('h2')[0]

    assert '{} {}'.format(person['vorname'], person['name']).decode(
        'utf-8') in soup.find_all('h4')[0].text

    # search for post
    rv = search(client, 'erster body')
    soup = BeautifulSoup(rv.data)

    assert 'erster body' in soup.find_all('h1')[0].text
    assert 'Posts' in soup.find_all('h2')[0]

    posts = [i.text for i in soup.find_all('div', class_='media-body')]

    for post in posts:
        assert 'erstes subject' in post
        assert 'erster body' in post

    # search for comment
    rv = search(client, 'kommentar')
    soup = BeautifulSoup(rv.data)

    assert 'kommentar' in soup.find_all('h1')[0].text
    assert 'Kommentare' in soup.find_all('h2')[0]

    comments = [i.text for i in soup.find_all('div', class_='media-body')]

    assert 'zweiter kommentar' in comments[0]
    assert 'erster kommentar' in comments[1]

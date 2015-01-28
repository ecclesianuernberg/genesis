# -*- coding: utf-8 -*-
import app
import tempfile
import os
import shutil
import base64
import json
import pytest
from config import config
from app import ct_connect, auth
from datetime import datetime
from cStringIO import StringIO
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer)
from passlib.hash import bcrypt
from PIL import Image
from random import choice


# loading config
app.app.config.from_object(config['testing'])

# get test user
TEST_USER = app.app.config['TEST_USER']


@pytest.fixture
def client(request):
    # create temp db file
    app.db.create_all()

    # create temp upload folder
    upload_dir = tempfile.mkdtemp()
    app.app.config['UPLOAD_FOLDER'] = upload_dir

    # create test client
    client = app.app.test_client()

    def fin():
        os.remove(app.app.config['SQLALCHEMY_DATABASE_URI'].split(
            'sqlite://')[1])

        # delete temp upload folder
        shutil.rmtree(app.app.config['UPLOAD_FOLDER'])

    request.addfinalizer(fin)
    return client


@pytest.fixture
def image(request):
    ''' creates temp image '''
    img = Image.new('RGB', (1000, 1000))
    temp_file = '{}.jpg'.format(tempfile.mktemp())
    img.save(temp_file)

    def fin():
        os.remove(temp_file)

    request.addfinalizer(fin)
    return temp_file


@pytest.fixture
def reset_ct_user(request):
    ''' reset ct user db entries '''
    # getting ids from the test user
    test_ids = [i['id'] for i in TEST_USER]

    # list of test user db entries
    ct_entries = [ct_connect.get_person_from_id(i)[0] for i in test_ids]

    # create data store and fill it
    test_user_data = []
    for entry in ct_entries:
        test_user_data.append(
            {'id': entry.id,
             'strasse': entry.strasse,
             'plz': entry.plz,
             'ort': entry.ort,
             'password': entry.password})

    def fin():
        for entry in test_user_data:
            user = ct_connect.get_person_from_id(entry['id'])[0]
            user.strasse = entry['strasse']
            user.plz = entry['plz']
            user.ort = entry['ort']
            user.password = entry['password']

            # save to db
            ct_connect.SESSION.add(user)
        ct_connect.SESSION.commit()

    request.addfinalizer(fin)
    return True


def get_wrong_user_id(own_id):
    ''' returns a id that is not own id '''
    ids = [i['id'] for i in TEST_USER]
    ids.remove(own_id)

    return choice(ids)


def login(client, email, password):
    ''' helper function to login '''
    return client.post('/login', data={
        'email': email,
        'password': password}, follow_redirects=True)


def logout(client):
    ''' helper function to logout '''
    return client.get('/logout', follow_redirects=True)


def add_prayer(client, body):
    ''' helper to add a new prayer '''
    return client.post('/prayer/add', data={
        'body': body,
        'active': True,
        'show_user': True}, follow_redirects=True)


def edit_prayer(client, id, body):
    ''' helper to edit a prayer '''
    return client.post('/prayer/{}/edit'.format(id),
                       data={'body': body}, follow_redirects=True)


def del_prayer(client, id):
    ''' helper to delete a prayer '''
    return client.get('/prayer/{}/del'.format(id),
                      follow_redirects=True)


def edit_group(client, id, description):
    ''' helper to edit group '''
    return client.post('/groups/{}/edit'.format(id), data={
        'description': description,
        'group_image': (StringIO('hi everyone'),
                        'test.jpg')}, follow_redirects=True)


def create_api_creds(test_user):
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(
        test_user['user'],
        test_user['password'])

    return base64.b64encode(user_password).decode(
        'utf-8').strip('\r\n')


def get_api_token(client, creds):
    return client.get('/api/token',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def create_wrong_api_creds(test_user):
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(
        test_user['user'],
        'wrongpassword')

    return base64.b64encode(user_password).decode(
        'utf-8').strip('\r\n')


def add_prayer_api(client, body, creds):
    ''' helper to add a new prayer '''
    return client.post('/api/prayer',
                       headers={'Authorization': 'Basic ' + creds},
                       data=json.dumps({'body': body,
                                        'active': True}),
                       content_type='application/json')


def edit_prayer_api(client, id, body, creds, active, show_user):
    ''' helper to add a new prayer '''
    return client.put('/api/prayer/{}'.format(id),
                      headers={'Authorization': 'Basic ' + creds},
                      data=json.dumps({'body': body,
                                       'active': active,
                                       'show_user': show_user}),
                      content_type='application/json')


def del_prayer_api(client, id, creds):
    ''' helper to delete prayer '''
    return client.delete('/api/prayer/{}'.format(id),
                         headers={'Authorization': 'Basic ' + creds},
                         content_type='application/json')


def edit_profile(client,
                 id,
                 street,
                 postal_code,
                 city,
                 bio,
                 password,
                 twitter,
                 facebook):
    return client.post('/profile/{}/edit'.format(id),
                       data={'street': street,
                             'postal_code': postal_code,
                             'city': city,
                             'bio': bio,
                             'twitter': twitter,
                             'facebook': facebook,
                             'password': password,
                             'confirm': password,
                             'user_image': (StringIO('hi everyone'),
                                            'test.jpg')},
                       follow_redirects=True)


@pytest.mark.parametrize('test_user', TEST_USER)
def test_login(client, test_user):
    ''' login user'''
    rv = login(client,
               test_user['user'],
               test_user['password'])

    assert rv.status_code == 200
    assert 'Erfolgreich eingeloggt!' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_logout(client, test_user):
    ''' logout user '''
    rv = logout(client)

    assert rv.status_code == 200
    assert 'Erfolgreich ausgeloggt!' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_ct_get_person(test_user):
    ''' person out of churchtools '''
    rv = ct_connect.get_person(test_user['user'])

    assert test_user['name'] in [i.name for i in rv]
    assert test_user['vorname'] in [i.vorname for i in rv]


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_ct_person_from_id(test_user):
    ''' person out of churchtools from id '''
    rv = ct_connect.get_person_from_id(test_user['id'])[0]

    assert rv.email == test_user['user']
    assert rv.name == test_user['name']
    assert rv.vorname == test_user['vorname']


def test_ct_get_active_groups():
    ''' list of active groups out of churchtools '''
    rv = ct_connect.get_active_groups()

    assert u'KG - Test' in [i.bezeichnung for i in rv]


def test_ct_get_group():
    ''' specific group out of churchtools '''
    rv = ct_connect.get_group(1)

    assert rv.valid_yn == 1
    assert rv.versteckt_yn == 0
    assert rv.bezeichnung == u'KG - Test'
    assert rv.gruendungsdatum == datetime(2010, 0o4, 0o6, 00, 00, 00)
    assert rv.treffzeit == u'Jeden Mittwoch 19h'
    assert rv.treffpunkt == u'Siebenkeesstr. 18, 90459 Nürnberg'
    assert rv.zielgruppe == u'Zwischen 9-17J.'
    assert rv.gruppentyp_id == 1
    assert rv.distrikt_id == 14
    assert rv.geolat == u'49.4412072'
    assert rv.geolng == u'11.078397799999948'
    assert rv.offen_yn == 0
    assert rv.oeffentlich_yn == 0
    assert rv.treffen_yn == 1
    assert rv.instatistik_yn == 1
    assert rv.mail_an_leiter_yn == 1
    assert rv.members_allowedmail_eachother_yn == 0
    assert rv.followup_typ_id == 0
    assert rv.fu_nachfolge_typ_id == 0
    assert rv.fu_nachfolge_objekt_id == 0
    assert rv.fu_nachfolge_gruppenteilnehmerstatus_id == 0


def test_ct_get_group_heads():
    ''' list of group heads out of churchtools '''
    rv = ct_connect.get_group_heads(1)

    assert [u'Leiter', u'Preuß'] == [i.name for i in rv]


def test_ct_get_group_members():
    ''' group members out of churchtools '''
    rv = ct_connect.get_group_members(1)

    assert [118, 163, 383] == [i.id for i in rv]


def test_ct_get_person_from_communityperson():
    ''' person object out of communityperson from churchtools '''
    rv = ct_connect.get_person_from_communityperson(118)

    assert rv.name == u'Leiter'
    assert rv.vorname == u'Test'
    assert rv.email == u'test.leiter@ecclesianuernberg.de'


@pytest.mark.parametrize('test_user', TEST_USER)
def test_ct_change_user_password(test_user):
    ''' change user password in churchtools '''
    # check if test_user password is the one in the churchtools-db
    db_user = ct_connect.get_person_from_id(test_user['id'])[0]

    assert bcrypt.verify(
        test_user['password'],
        db_user.password)

    # new password
    password = 'newpassword'
    ct_connect.change_user_password(test_user['id'], password)
    db_user = ct_connect.get_person_from_id(test_user['id'])[0]

    assert bcrypt.verify(
        password,
        db_user.password)

    # reset password
    ct_connect.change_user_password(test_user['id'], test_user['password'])


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_prayer(client, test_user):
    ''' access to random prayer '''
    # not logged in
    rv = client.get('/prayer')

    assert rv.status_code == 302

    # logged in
    login(client,
          test_user['user'],
          test_user['password'])

    rv = client.get('/prayer')

    assert rv.status_code == 200


@pytest.mark.parametrize('test_user', TEST_USER)
def test_add_prayer(client, test_user):
    ''' adding prayer '''
    login(client,
          test_user['user'],
          test_user['password'])

    prayer = 'Test-Anliegen'
    rv = add_prayer(client, prayer)

    assert rv.status_code == 200
    assert 'Gebetsanliegen abgeschickt!' in rv.data
    assert prayer in rv.data

    # check db entry
    db_entry = app.views.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is True
    assert db_entry.show_user is True


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_prayer(client, test_user):
    ''' editing prayer '''
    login(client,
          test_user['user'],
          test_user['password'])

    # add prayer
    prayer = 'Test-Anliegen'
    rv = add_prayer(client, prayer)

    prayer = 'Neues Anliegen'
    rv = edit_prayer(client, 1, prayer)

    assert rv.status_code == 200
    assert 'Gebetsanliegen veraendert!' in rv.data
    assert prayer in rv.data

    # check db entry
    db_entry = app.views.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is False
    assert db_entry.show_user is False


@pytest.mark.parametrize('test_user', TEST_USER)
def test_del_prayer(client, test_user):
    '''delete prayer'''
    login(client,
          test_user['user'],
          test_user['password'])

    # add prayer to delete it
    add_prayer(client, 'Ein Test zum entfernen')

    rv = del_prayer(client, 1)

    assert rv.status_code == 200
    assert 'Gebetsanliegen entfernt!' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_group_list(client, test_user):
    ''' access group list '''
    # not logged in
    rv = client.get('/groups')

    assert rv.status_code == 302

    # logged in

    login(client,
          test_user['user'],
          test_user['password'])

    rv = client.get('/groups')

    assert rv.status_code == 200


def test_group_edit_forbidden_logged_in(client):
    ''' logged in user cant access groups edit pages '''
    urls = ['/groups/{}/edit'.format(group.id)
            for group in ct_connect.get_active_groups() if group.id != 1]

    for url in urls:
        login(client,
              app.app.config['TEST_USER'][0]['user'],
              app.app.config['TEST_USER'][0]['password'])

        rv = client.get(url)

        assert rv.status_code == 403


def test_group_edit_forbidden_logged_out(client):
    ''' logged out user cant access group edit pages '''
    urls = ['/groups/{}/edit'.format(
        i.id) for i in ct_connect.get_active_groups()]

    for url in urls:
        rv = client.get(url)

        assert 'You should be redirected automatically' in rv.data


def test_group_edit_allowed(client):
    ''' user can edit groups he is head of '''

    # list of active groups
    groups = ct_connect.get_active_groups()

    # list of groups the test user is head of
    head_groups = [i.id
                   for i in groups
                   for j in ct_connect.get_group_heads(i.id) if j.id == 118]

    # run tests for each group the test user is head of
    for group in head_groups:
        # login
        login(client,
              app.app.config['TEST_USER'][0]['user'],
              app.app.config['TEST_USER'][0]['password'])

        # edit
        rv = edit_group(client, group, 'Dies ist ein Test')

        assert rv.status_code == 200
        assert 'Dies ist ein Test' in rv.data
        assert 'Gruppe geaendert' in rv.data


def test_group_edit_forbidden(client):
    ''' user cant edit groups he isnt head of '''
    # list of active groups
    groups = ct_connect.get_active_groups()

    # list of groups the logged in user is not a head of
    no_head_groups = []
    for group in groups:
        if 118 not in [head.id
                       for head in ct_connect.get_group_heads(group.id)]:
            no_head_groups.append(group.id)

    # test it
    for group in no_head_groups:
        # login
        login(client,
              app.app.config['TEST_USER'][0]['user'],
              app.app.config['TEST_USER'][0]['password'])

        # edit
        rv = edit_group(client, group, 'Dies ist ein Test')

        assert rv.status_code == 403


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_token(client, test_user):
    ''' get valid token '''
    creds = create_api_creds(test_user)
    rv = get_api_token(client, creds)

    assert rv.status_code == 200

    token = json.loads(rv.data)['token']
    s = Serializer(app.app.config['SECRET_KEY'])

    assert s.loads(token)['id'] == test_user['user']

    # wrong password
    creds = create_wrong_api_creds(test_user)
    rv = get_api_token(client, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_add_prayer(client, test_user):
    ''' add prayer through api '''
    creds = create_api_creds(test_user)
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == 'anonym'
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong password
    creds = create_wrong_api_creds(test_user)
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_edit_prayer(client, test_user):
    ''' edit prayer through api '''
    creds = create_api_creds(test_user)
    body = 'Noch ein Test'
    active = True
    show_user = False

    # add prayer
    add_prayer_api(client, 'Test', creds)

    # edit prayer
    rv = edit_prayer_api(client, 1, body, creds, active, show_user)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == 'anonym'
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Noch ein Test'

    # wrong password
    creds = create_wrong_api_creds(test_user)
    body = 'Test'
    rv = edit_prayer_api(client, 1, body, creds, active, show_user)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_del_prayer(client, test_user):
    ''' delete prayer through api '''
    creds = create_api_creds(test_user)

    # add prayer
    add_prayer_api(client, 'Test', creds)

    rv = del_prayer_api(client, 1, creds)
    assert rv.status_code == 204

    rv = del_prayer_api(client, 20, creds)
    assert rv.status_code == 404


def test_persons():
    ''' creates session dict for persons '''
    test_user = app.app.config['TEST_USER'][1]
    user = ct_connect.get_person(test_user['user'])
    persons = auth.persons(user)
    assert persons[0]['email'] == test_user['user']
    assert persons[0]['id'] == test_user['id']
    assert persons[0]['vorname'] == test_user['vorname']
    assert persons[0]['name'] == test_user['name']


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_navbar_profile_links(client, test_user):
    ''' profile link in navbar '''
    rv = client.get('/')
    assert '{} {}'.format(
        test_user['vorname'],
        test_user['name']) not in rv.data

    # now login
    login(client,
          test_user['user'],
          test_user['password'])

    rv = client.get('/')
    assert '{} {}'.format(
        test_user['vorname'],
        test_user['name']) in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_valid_users(test_user):
    ''' list of valid users '''
    user = auth.CTUser(
        uid=test_user['user'],
        password=test_user['password']).get_user()

    assert auth.get_valid_users(
        user,
        test_user['password'])

    # wrong password
    user = auth.CTUser(
        uid=test_user['user'],
        password='wrongpassword').get_user()

    assert not auth.get_valid_users(
        user,
        'wrongpassword')


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_access_profile(client, test_user):
    ''' access profiles '''
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 302

    # now login
    login(client, test_user['user'], test_user['password'])
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 200
    assert '<h1>{} {}'.format(
        test_user['vorname'], test_user['name']) in rv.data

    # not exisiting profile
    rv = client.get('/profile/7777')
    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_profile_edit(client, test_user):
    ''' access profile edit form '''
    # not logged in
    rv = client.get('/profile/{}/edit'.format(test_user['id']))
    assert rv.status_code == 302

    # logged in try to edit other profile
    login(client, test_user['user'], test_user['password'])

    rv = client.get('/profile/{}/edit'.format(
        get_wrong_user_id(test_user['id'])))
    assert rv.status_code == 403

    # own profile edit
    rv = client.get('/profile/{}/edit'.format(test_user['id']))
    assert rv.status_code == 200


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile_button(client, test_user):
    login(client, test_user['user'], test_user['password'])

    rv = client.get('/profile/{}'.format(
        get_wrong_user_id(test_user['id'])))
    assert 'edit' not in rv.data

    rv = client.get('/profile/{}'.format(test_user['id']))
    assert 'edit' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile(client, reset_ct_user, test_user):
    ''' edit profile '''
    login(client, test_user['user'], test_user['password'])

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
                      facebook=facebook)

    assert rv.status_code == 200
    assert 'Profil geaendert' in rv.data

    # test profile page
    assert city in rv.data
    assert bio in rv.data
    assert twitter in rv.data
    assert facebook in rv.data
    assert test_user['user'] in rv.data

    # test churchtools db entries
    ct_person = ct_connect.get_person_from_id(test_user['id'])[0]

    assert ct_person.strasse == street
    assert ct_person.plz == postal_code
    assert ct_person.ort == city

    # check password
    assert bcrypt.verify(password, ct_person.password)


def test_image_resize(image):
    img_out = '{}.jpg'.format(tempfile.mktemp())
    app.views.image_resize(image, img_out, size=800)
    rv = Image.open(img_out)

    assert rv.size == (800, 800)


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
                              user=test_user['user'])

    # returns a uuid
    assert rv

    # file list with resized image and thumbnail in it
    assert '{}.jpg'.format(rv) \
        and '{}-thumb.jpg'.format(rv) \
        in os.listdir(app.app.config['UPLOAD_FOLDER'])

    # checks db entries
    image = app.models.Image.query.first()

    assert image.user == test_user['user']
    assert image.upload_to == 'test'

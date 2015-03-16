# -*- coding: utf-8 -*-
import os

# set environment variables
os.environ['FLASK_CONFIG'] = 'testing'

import app
import flask
import tempfile
import os
import shutil
import base64
import json
import pytest
from config import config
from app import ct_connect, auth, mailing
from datetime import datetime
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer)
from passlib.hash import bcrypt
from PIL import Image
from random import choice
from unidecode import unidecode
from bs4 import BeautifulSoup


# loading config
app.app.config.from_object(config['testing'])

# get test user
TEST_USER = app.app.config['TEST_USER']


@pytest.fixture
def db(request):
    ''' creates tables and drops them for every test '''
    app.db.create_all()

    def fin():
        app.db.session.commit()
        app.db.drop_all()

    request.addfinalizer(fin)


@pytest.fixture
def client(db, request):
    # create temp upload folder
    upload_dir = tempfile.mkdtemp()
    app.app.config['UPLOAD_FOLDER'] = upload_dir

    # create test client
    client = app.app.test_client()

    def fin():
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
        user_data = {}
        user_data['id'] = entry.id
        user_data['strasse'] = entry.strasse
        user_data['plz'] = entry.plz
        user_data['ort'] = entry.ort
        user_data['password'] = entry.password

        test_user_data.append(user_data)

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


@pytest.fixture
def reset_ct_group(request):
    ''' reset test group data in db '''
    # getting group out of churchtools db
    group = ct_connect.get_group(1)

    # create data store and fill it
    group_data = {}
    group_data['treffpunkt'] = group.treffpunkt
    group_data['treffzeit'] = group.treffzeit
    group_data['zielgruppe'] = group.zielgruppe

    def fin():
        group.treffpunkt = group_data['treffpunkt']
        group.treffzeit = group_data['treffzeit']
        group.zielgruppe = group_data['zielgruppe']

        # save back to ct
        ct_connect.SESSION.add(group)
        ct_connect.SESSION.commit()

    request.addfinalizer(fin)


def ct_create_person(user_data):
    ''' creates temp churchtools person '''
    # extracting column keys out of person table from churchtools
    ct_columns = ct_connect.Person.__table__.columns.keys()

    # create person data dict prefilled with default empty strings
    person_data = {}
    for column in ct_columns:
        person_data[column] = ''

    # for each item in user_data create an db entry
    for user in user_data:
        # getting person_data dict
        temp_person_data = person_data

        # fill the temp_person_dict
        for key, value in user.iteritems():
            if key == 'password':
                temp_person_data[key] = bcrypt.encrypt(value)
            else:
                temp_person_data[key] = value

        # define temp user
        temp_user = ct_connect.Person(**temp_person_data)

        # add temp user to session
        ct_connect.SESSION.add(temp_user)

    # save to db
    ct_connect.SESSION.commit()


def ct_delete_person(user_data):
    # for each user in user_data find and delete entry
    for user in user_data:
        ct_connect.SESSION.query(ct_connect.Person).filter(
            ct_connect.Person.email == user['email'],
            ct_connect.Person.name == user['name'],
            ct_connect.Person.vorname == user['vorname']).delete()

    # save to db
    ct_connect.SESSION.commit()


@pytest.fixture
def ct_same_username_and_password(request):
    user_data = [{'email': 'test@test.com',
                  'password': 'testpassword',
                  'vorname': 'Testvorname',
                  'name': 'Testnachname'},
                 {'email': 'test@test.com',
                  'password': 'testpassword',
                  'vorname': 'AnotherTestvorname',
                  'name': 'AnotherTestnachname'}]

    ct_create_person(user_data)

    def fin():
        ct_delete_person(user_data)

    request.addfinalizer(fin)
    return user_data


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


def edit_prayer(client, id, body, active=False, show_user=False):
    ''' helper to edit a prayer '''
    # i discovered some strange behaviour or it was just my head that got
    # twisted. just sending body data it means that the booleanfields are
    # not toggled at all. i could send something like "active: True" or even
    # "active: 'foo" to get a booleanfield data sent to the form. and now
    # even more bizarr: you can send "active: False" and it returns in a True.
    if active and show_user:
        return client.post('/prayer/mine',
                           data={'{}-body'.format(id): body,
                                 '{}-active'.format(id): True,
                                 '{}-show_user'.format(id): True},
                           follow_redirects=True)

    elif active:
        return client.post('/prayer/mine',
                           data={'{}-body'.format(id): body,
                                 '{}-active'.format(id): True},
                           follow_redirects=True)

    elif show_user:
        return client.post('/prayer/mine',
                           data={'{}-body'.format(id): body,
                                 '{}-show_user'.format(id): True},
                           follow_redirects=True)

    else:
        return client.post('/prayer/mine',
                           data={'{}-body'.format(id): body},
                           follow_redirects=True)


def del_prayer(client, id):
    ''' helper to delete a prayer '''
    return client.get('/prayer/{}/del'.format(id),
                      follow_redirects=True)


def edit_group(client, id, description, where, when, audience, image):
    ''' helper to edit group '''
    with open(image) as f:
        return client.post('/group/{}'.format(id),
                           data={'description': description,
                                 'group_image': (f, 'test.jpg'),
                                 'where': where,
                                 'when': when,
                                 'audience': audience},
                           follow_redirects=True)


def create_api_creds(username, password):
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(
        username,
        password)

    return base64.b64encode(user_password).decode(
        'utf-8').strip('\r\n')


def get_api_token(client, creds):
    return client.get('/api/token',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


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
                 facebook,
                 image):
    with open(image) as f:
        return client.post('/profile/{}'.format(id),
                           data={'street': street,
                                 'postal_code': postal_code,
                                 'city': city,
                                 'bio': bio,
                                 'twitter': twitter,
                                 'facebook': facebook,
                                 'password': password,
                                 'confirm': password,
                                 'user_image': (f, 'test.jpg')},
                           follow_redirects=True)


def send_mail(client, url, subject, body):
    return client.post(url,
                       data={'subject': subject,
                             'body': body},
                       follow_redirects=True)


@pytest.mark.parametrize('test_user', TEST_USER)
def test_login(client, test_user):
    ''' login user'''
    with client as c:
        rv = login(c, test_user['email'], test_user['password'])

        assert rv.status_code == 200
        assert 'Erfolgreich eingeloggt!' in rv.data
        assert flask.session['user'][0]['active'] is True


@pytest.mark.parametrize('test_user', TEST_USER)
def test_logout(client, test_user):
    ''' logout user '''
    rv = logout(client)

    assert rv.status_code == 200
    assert 'Erfolgreich ausgeloggt!' in rv.data


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_ct_get_person(test_user):
    ''' person out of churchtools '''
    rv = ct_connect.get_person(test_user['email'])

    assert test_user['name'] in [i.name for i in rv]
    assert test_user['vorname'] in [i.vorname for i in rv]


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_ct_person_from_id(test_user):
    ''' person out of churchtools from id '''
    rv = ct_connect.get_person_from_id(test_user['id'])[0]

    assert rv.email == test_user['email']
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
          test_user['email'],
          test_user['password'])

    rv = client.get('/prayer')

    assert rv.status_code == 200


def test_random_prayer(client):
    ''' random prayer view '''
    test_user = TEST_USER[1]
    prayer = 'Dies ist ein Test!'

    login(client, test_user['email'], test_user['password'])
    add_prayer(client, prayer)

    # prayer with show_user
    rv = client.get('/prayer')
    soup = BeautifulSoup(rv.data)

    assert '{} {}'.format(
        test_user['vorname'],
        test_user['name']) == soup.find_all('div',
                                            class_='panel-heading')[0].text

    # prayer body
    assert prayer in soup.find_all('div',
                                   class_='panel-body')[0].text

    # prayer with unabled show_user
    edit_prayer(client, 1, prayer, active=True)
    rv = client.get('/prayer')
    soup = BeautifulSoup(rv.data)

    assert soup.find_all('div',
                         class_='panel-heading')[0].text == ''


@pytest.mark.parametrize('test_user', TEST_USER)
def test_add_prayer(client, test_user):
    ''' adding prayer '''
    login(client,
          test_user['email'],
          test_user['password'])

    prayer = 'Test-Anliegen'
    rv = add_prayer(client, prayer)

    assert rv.status_code == 200
    assert 'Gebetsanliegen abgeschickt!' in rv.data
    assert prayer in rv.data

    # check db entry
    db_entry = app.models.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is True
    assert db_entry.show_user is True


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_prayer(client, test_user):
    ''' editing prayer '''
    login(client,
          test_user['email'],
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
    db_entry = app.models.get_prayer(1)

    assert db_entry.body == prayer
    assert db_entry.active is False
    assert db_entry.show_user is False


@pytest.mark.parametrize('test_user', TEST_USER)
def test_del_prayer(client, test_user):
    '''delete prayer'''
    login(client,
          test_user['email'],
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
          test_user['email'],
          test_user['password'])

    rv = client.get('/groups')

    assert rv.status_code == 200


@pytest.mark.parametrize('test_user', TEST_USER)
def test_group_list(client, test_user):
    ''' group list data '''
    group_data = []

    # ct group data
    for group in ct_connect.get_active_groups():
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
    login(client,
          test_user['email'],
          test_user['password'])

    rv = client.get('/group/1')

    assert rv.status_code == 200


@pytest.mark.parametrize('own_group',
                         [i.id
                          for i in ct_connect.get_active_groups()
                          for j in ct_connect.get_group_heads(i.id)
                          if j.id == 118])
def test_group_edit_allowed(client, reset_ct_group, own_group, image):
    ''' user can edit groups he is head of '''
    test_user = TEST_USER[0]

    # login
    login(client,
          test_user['email'],
          test_user['password'])

    # edit
    rv = edit_group(client,
                    own_group,
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


@pytest.mark.parametrize(
    'not_own_group',
    [i.id
     for i in ct_connect.get_active_groups()
     if 118 not in [j.id for j in ct_connect.get_group_heads(i.id)]])
def test_group_edit_forbidden(client, not_own_group, image):
    ''' user cant edit groups he isnt head of '''
    test_user = TEST_USER[0]

    # login
    login(client,
          test_user['email'],
          test_user['password'])

    # edit
    rv = edit_group(client,
                    not_own_group,
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
    groups = ct_connect.get_active_groups()
    random_group = choice(groups)

    group_ct_data = ct_connect.get_group(random_group.id)

    login(client, test_user['email'], test_user['password'])

    rv = client.get('/group/{}'.format(random_group.id))

    assert group_ct_data.bezeichnung.split('-')[-1].encode('utf-8') in rv.data
    if group_ct_data.treffzeit:
        assert group_ct_data.treffzeit.encode('utf-8') in rv.data
    if group_ct_data.treffpunkt:
        assert group_ct_data.treffpunkt.encode('utf-8') in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_token(client, test_user):
    ''' get valid token '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_api_token(client, creds)

    assert rv.status_code == 200

    token = json.loads(rv.data)['token']
    s = Serializer(app.app.config['SECRET_KEY'])

    assert s.loads(token)['id'] == test_user['email']

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    rv = get_api_token(client, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_add_prayer(client, test_user):
    ''' add prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == 'anonym'
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 401

    # check db entry
    db_entry = app.models.get_prayer(1)
    assert db_entry.id == 1
    assert db_entry.body == 'Test'
    assert db_entry.user == test_user['id']
    assert db_entry.active is True


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_add_prayer_token(client, test_user):
    ''' add prayer through api with a auth token '''
    # get token
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_api_token(client, creds)
    token = json.loads(rv.data)['token']

    # auth with token
    creds = create_api_creds(token, 'foo')
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == 'anonym'
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong token
    token = 'wrongtoken'
    creds = create_api_creds(token, 'foo')
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_edit_prayer(client, test_user):
    ''' edit prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])
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
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    body = 'Test'
    rv = edit_prayer_api(client, 1, body, creds, active, show_user)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_api_del_prayer(client, test_user):
    ''' delete prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])

    # add prayer
    add_prayer_api(client, 'Test', creds)

    rv = del_prayer_api(client, 1, creds)
    assert rv.status_code == 204

    rv = del_prayer_api(client, 20, creds)
    assert rv.status_code == 404


def test_persons():
    ''' creates session dict for persons '''
    test_user = app.app.config['TEST_USER'][1]
    user = ct_connect.get_person(test_user['email'])
    persons = auth.persons(user)
    assert persons[0]['email'] == test_user['email']
    assert persons[0]['id'] == test_user['id']
    assert persons[0]['vorname'] == test_user['vorname']
    assert persons[0]['name'] == test_user['name']


@pytest.mark.parametrize('test_user', TEST_USER)
def test_navbar_profile_links(client, test_user):
    ''' profile link in navbar '''
    rv = client.get('/')
    assert '{} {}'.format(
        test_user['vorname'],
        test_user['name']) not in rv.data

    # now login
    login(client,
          test_user['email'],
          test_user['password'])

    rv = client.get('/')
    assert '{} {}'.format(
        test_user['vorname'],
        test_user['name']) in rv.data


def test_navbar_profile_links_same_auth(client, ct_same_username_and_password):
    ''' profile links in navbar for same email password combination '''
    test_user = ct_same_username_and_password[0]

    login(client, test_user['email'], test_user['password'])

    rv = client.get('/')

    for user in ct_same_username_and_password:
        assert '{} {}'.format(
            user['vorname'],
            user['name']) in rv.data


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_valid_users(test_user):
    ''' list of valid users '''
    user = auth.CTUser(
        uid=test_user['email'],
        password=test_user['password']).get_user()

    assert auth.get_valid_users(
        user,
        test_user['password'])

    # wrong password
    user = auth.CTUser(
        uid=test_user['email'],
        password='wrongpassword').get_user()

    assert not auth.get_valid_users(
        user,
        'wrongpassword')


@pytest.mark.parametrize('test_user', TEST_USER)
def test_access_profile(client, test_user):
    ''' access profiles '''
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 302

    # now login
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/profile/{}'.format(test_user['id']))

    assert rv.status_code == 200
    assert '<h1>{} {}'.format(
        test_user['vorname'], test_user['name']) in rv.data
    assert 'avatar.png' in rv.data

    # not exisiting profile
    rv = client.get('/profile/7777')
    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile_button(client, test_user):
    login(client, test_user['email'], test_user['password'])

    rv = client.get('/profile/{}'.format(
        get_wrong_user_id(test_user['id'])))
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
    ct_person = ct_connect.get_person_from_id(test_user['id'])[0]

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
        c.get('/profile/1')

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

    for view in ['newsview',
                 'groupmetadataview',
                 'usermetadataview',
                 'imageview',
                 'prayerview']:
        rv = client.get('/admin/{}/'.format(view))
        assert rv.status_code == status_code


def test_admin_access_logged_out(client):
    for view in ['newsview',
                 'groupmetadataview',
                 'usermetadataview',
                 'imageview',
                 'prayerview']:
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
    assert rv == ['test.leiter@ecclesianuernberg.de',
                  'xsteadfastx@gmail.com']


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
        rv = send_mail(client,
                       '/mail/profile/{}'.format(test_user['id']),
                       'Testsubject',
                       'Testbody')

        assert rv.status_code == 200
        assert 'Email gesendet!' in rv.data
        assert outbox[0].sender == '{} {} <{}>'.format(
            unidecode(test_user['vorname'].decode('utf-8')),
            unidecode(test_user['name'].decode('utf-8')),
            test_user['email'])
        assert outbox[0].recipients == recipients
        assert outbox[0].subject == subject
        assert body in outbox[0].body

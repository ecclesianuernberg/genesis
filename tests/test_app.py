# -*- coding: utf-8 -*-
import app
import tempfile
import os
import shutil
import base64
import json
import pytest
from config import config
from app import ct_connect
from datetime import datetime
from cStringIO import StringIO
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer)


@pytest.fixture
def client(request):
    # loading config
    app.app.config.from_object(config['testing'])

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


def create_api_creds():
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(
        app.app.config['TEST_USER']['user'],
        app.app.config['TEST_USER']['password'])

    return base64.b64encode(user_password).decode(
        'utf-8').strip('\r\n')


def get_api_token(client, creds):
    return client.get('/api/token',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def create_wrong_api_creds():
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(
        app.app.config['TEST_USER']['user'],
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


def test_login(client):
    ''' login user'''
    rv = login(client,
               app.app.config['TEST_USER']['user'],
               app.app.config['TEST_USER']['password'])

    assert rv.status_code == 200
    assert 'Erfolgreich eingeloggt!' in rv.data


def test_logout(client):
    ''' logout user '''
    rv = logout(client)

    assert rv.status_code == 200
    assert 'Erfolgreich ausgeloggt!' in rv.data


def test_ct_get_person():
    ''' person out of churchtools '''
    rv = ct_connect.get_person('test.leiter@ecclesianuernberg.de')

    assert rv.name == u'Leiter'
    assert rv.vorname == u'Test'


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


def test_access_prayer(client):
    ''' access to random prayer '''
    # not logged in
    rv = client.get('/prayer')

    assert rv.status_code == 302

    # logged in
    login(client,
          app.app.config['TEST_USER']['user'],
          app.app.config['TEST_USER']['password'])

    rv = client.get('/prayer')

    assert rv.status_code == 200


def test_add_prayer(client):
    ''' adding prayer '''
    login(client,
          app.app.config['TEST_USER']['user'],
          app.app.config['TEST_USER']['password'])

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


def test_edit_prayer(client):
    ''' editing prayer '''
    login(client,
          app.app.config['TEST_USER']['user'],
          app.app.config['TEST_USER']['password'])

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


def test_del_prayer(client):
    '''delete prayer'''
    login(client,
          app.app.config['TEST_USER']['user'],
          app.app.config['TEST_USER']['password'])

    # add prayer to delete it
    add_prayer(client, 'Ein Test zum entfernen')

    rv = del_prayer(client, 1)

    assert rv.status_code == 200
    assert 'Gebetsanliegen entfernt!' in rv.data


def test_access_group_list(client):
    ''' access group list '''
    # not logged in
    rv = client.get('/groups')

    assert rv.status_code == 302

    # logged in

    login(client,
          app.app.config['TEST_USER']['user'],
          app.app.config['TEST_USER']['password'])

    rv = client.get('/groups')

    assert rv.status_code == 200


def test_group_edit_forbidden_logged_in(client):
    ''' logged in user cant access groups edit pages '''
    urls = ['/groups/{}/edit'.format(group.id)
            for group in ct_connect.get_active_groups() if group.id != 1]

    for url in urls:
        login(client,
              app.app.config['TEST_USER']['user'],
              app.app.config['TEST_USER']['password'])

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
              app.app.config['TEST_USER']['user'],
              app.app.config['TEST_USER']['password'])

        # edit
        rv = edit_group(client, group, 'Dies ist ein Test')

        assert rv.status_code == 200
        assert 'Dies ist ein Test' in rv.data


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
              app.app.config['TEST_USER']['user'],
              app.app.config['TEST_USER']['password'])

        # edit
        rv = edit_group(client, group, 'Dies ist ein Test')

        assert rv.status_code == 403


def test_api_token(client):
    ''' get valid token '''
    creds = create_api_creds()
    rv = get_api_token(client, creds)

    assert rv.status_code == 200

    token = json.loads(rv.data)['token']
    s = Serializer(app.app.config['SECRET_KEY'])

    assert s.loads(token)['id'] == app.app.config['TEST_USER']['user']

    # wrong password
    creds = create_wrong_api_creds()
    rv = get_api_token(client, creds)

    assert rv.status_code == 401


def test_api_add_prayer(client):
    ''' add prayer through api '''
    creds = create_api_creds()
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == 'anonym'
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong password
    creds = create_wrong_api_creds()
    body = 'Test'
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 401


def test_api_edit_prayer(client):
    ''' edit prayer through api '''
    creds = create_api_creds()
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
    creds = create_wrong_api_creds()
    body = 'Test'
    rv = edit_prayer_api(client, 1, body, creds, active, show_user)

    assert rv.status_code == 401


def test_api_del(client):
    ''' delete prayer through api '''
    creds = create_api_creds()

    # add prayer
    add_prayer_api(client, 'Test', creds)

    rv = del_prayer_api(client, 1, creds)
    assert rv.status_code == 204

    rv = del_prayer_api(client, 20, creds)
    assert rv.status_code == 404

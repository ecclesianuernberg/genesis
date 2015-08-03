# -*- coding: utf-8 -*-
import pytest
import json
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)
from app import APP, ct_connect, models
from helper import (create_api_creds, get_api_token, add_prayer_api,
                    edit_prayer_api, del_prayer_api, get_prayer_api,
                    get_group_overview_api, get_group_item_api,
                    edit_group_item_api, edit_group_item_api_avatar,
                    get_profile_api, edit_profile_api, edit_profile_api_avatar)


# get test user
TEST_USER = APP.config['TEST_USER']


@pytest.mark.parametrize('test_user', TEST_USER)
def test_token(client, test_user):
    ''' get valid token '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_api_token(client, creds)

    assert rv.status_code == 200

    token = json.loads(rv.data)['token']
    s = Serializer(APP.config['SECRET_KEY'])

    assert s.loads(token)['id'] == test_user['email']

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    rv = get_api_token(client, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_add_prayer(client, test_user):
    ''' add prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    body = 'Test'
    name = 'Testname'

    rv = add_prayer_api(client, body, creds, name)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == name
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    rv = add_prayer_api(client, body, creds, name)

    assert rv.status_code == 401

    # check db entry
    db_entry = models.get_prayer(1)
    assert db_entry.id == 1
    assert db_entry.body == body
    assert db_entry.user_id == test_user['id']
    assert db_entry.active is True
    assert db_entry.name == name


@pytest.mark.parametrize('test_user', TEST_USER)
def test_add_prayer_token(client, test_user):
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

    assert data_dict.get('name') == ''
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Test'

    # wrong token
    token = 'wrongtoken'
    creds = create_api_creds(token, 'foo')
    rv = add_prayer_api(client, body, creds)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_prayer(client, test_user):
    ''' edit prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    body = 'Noch ein Test'
    active = True
    name = 'Testname'

    # add prayer
    add_prayer_api(client, 'Test', creds)

    # edit prayer
    rv = edit_prayer_api(client, 1, body, creds, active, name)

    assert rv.status_code == 200

    # create dict out of json response
    data_dict = json.loads(rv.data)

    assert data_dict.get('name') == name
    assert data_dict.get('id') == 1
    assert data_dict.get('prayer') == 'Noch ein Test'

    # wrong prayer
    rv = edit_prayer_api(client, 20, body, creds, active, name)

    assert rv.status_code == 404

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrongpassword')
    body = 'Test'
    rv = edit_prayer_api(client, 1, body, creds, active, name)

    assert rv.status_code == 401


@pytest.mark.parametrize('test_user', TEST_USER)
def test_del_prayer(client, test_user):
    ''' delete prayer through api '''
    creds = create_api_creds(test_user['email'], test_user['password'])

    # add prayer
    add_prayer_api(client, 'Test', creds)

    rv = del_prayer_api(client, 1, creds)
    assert rv.status_code == 204

    rv = del_prayer_api(client, 20, creds)
    assert rv.status_code == 404


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_prayer(client, test_user):
    ''' get random prayer '''
    creds = create_api_creds(test_user['email'], test_user['password'])
    body = 'Test'
    name = 'Testname'

    # no prayer there
    rv = get_prayer_api(client, creds)

    assert rv.status_code == 404

    # add prayer
    add_prayer_api(client, body, creds, name)
    rv = get_prayer_api(client, creds)

    assert rv.status_code == 200

    data_dict = json.loads(rv.data)

    assert data_dict['prayer'] == body
    assert data_dict['name'] == name


@pytest.mark.parametrize('test_user', TEST_USER)
def test_group_overview_authorized(client, test_user):
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_group_overview_api(client, creds)

    assert rv.status_code == 200

    with ct_connect.session_scope() as ct_session:
        assert len(ct_connect.get_active_groups(ct_session)) == len(
            json.loads(rv.data)['groups'])

        for group in json.loads(rv.data)['groups']:
            group_ct = ct_connect.get_group(ct_session, group['id'])
            group_metadata = models.get_group_metadata(group['id'])

            assert group['name'] == group_ct.bezeichnung.split(' - ')[-1]
            assert group['id'] == group_ct.id

            for attribute in ['treffzeit', 'treffpunkt', 'zielgruppe', 'notiz']:
                if group_ct.__dict__[attribute] == '':
                    assert group[attribute] is None
                else:
                    assert group[attribute] == group_ct.__dict__[attribute]

            if group['avatar_id']:
                assert group['avatar_id'] == group_metadata.avatar_id

            if group['description']:
                assert group['description'] == group_metadata.description


def test_group_overview_unauthorized(client):
    rv = client.get('/api/groups')

    assert rv.status_code == 200

    with ct_connect.session_scope() as ct_session:
        assert len(ct_connect.get_active_groups(ct_session)) == len(
            json.loads(rv.data)['groups'])

        for group in json.loads(rv.data)['groups']:
            group_ct = ct_connect.get_group(ct_session, group['id'])
            group_metadata = models.get_group_metadata(group['id'])

            assert group['name'] == group_ct.bezeichnung.split(' - ')[-1]
            assert group['id'] == group_ct.id

            assert group['treffpunkt'] is None

            for attribute in ['treffzeit', 'zielgruppe', 'notiz']:
                if group_ct.__dict__[attribute] == '':
                    assert group[attribute] is None
                else:
                    assert group[attribute] == group_ct.__dict__[attribute]

            if group['avatar_id']:
                assert group['avatar_id'] == group_metadata.avatar_id

            if group['description']:
                assert group['description'] == group_metadata.description


def test_group_overview_wrong_password(client):
    creds = create_api_creds(TEST_USER[0]['email'], 'wrong')
    rv = get_group_overview_api(client, creds)

    assert rv.status_code == 200

    with ct_connect.session_scope() as ct_session:
        assert len(ct_connect.get_active_groups(ct_session)) == len(
            json.loads(rv.data)['groups'])

        for group in json.loads(rv.data)['groups']:
            group_ct = ct_connect.get_group(ct_session, group['id'])
            group_metadata = models.get_group_metadata(group['id'])

            assert group['name'] == group_ct.bezeichnung.split(' - ')[-1]
            assert group['id'] == group_ct.id

            assert group['treffpunkt'] is None

            for attribute in ['treffzeit', 'zielgruppe', 'notiz']:
                if group_ct.__dict__[attribute] == '':
                    assert group[attribute] is None
                else:
                    assert group[attribute] == group_ct.__dict__[attribute]

            if group['avatar_id']:
                assert group['avatar_id'] == group_metadata.avatar_id

            if group['description']:
                assert group['description'] == group_metadata.description


@pytest.mark.parametrize('test_user', TEST_USER)
def test_get_group_item(client, test_user):
    # unauthorized
    rv = client.get('/api/group/1')

    assert rv.status_code == 401

    # wrong password
    creds = create_api_creds(test_user['email'], 'wrong')
    rv = get_group_item_api(client, creds, 1)

    assert rv.status_code == 401

    # valid userdata
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_group_item_api(client, creds, 1)

    assert rv.status_code == 200

    rv_json = json.loads(rv.data)['group']

    with ct_connect.session_scope() as ct_session:
        group_ct = ct_connect.get_group(ct_session, 1)
        group_metadata = models.get_group_metadata(1)

        assert rv_json['name'] == group_ct.bezeichnung.split(' - ')[-1]
        assert rv_json['id'] == group_ct.id

        if rv_json['description']:
            assert rv_json['description'] == group_metadata.description

        for attribute in ['treffzeit', 'treffpunkt', 'zielgruppe', 'notiz']:
            if group_ct.__dict__[attribute] == '':
                assert rv_json[attribute] is None
            else:
                assert rv_json[attribute] == group_ct.__dict__[attribute]

        if rv_json['avatar_id']:
            assert rv.json['avatar_id'] == group_metadata.avatar_id


def test_edit_group_item(client, reset_ct_group):
    description = 'Testdescription'
    treffpunkt = 'Testtreffpunkt'
    treffzeit = 'Testtreffzeit'
    zielgruppe = 'Testzielgruppe'

    # unauthorized
    creds = create_api_creds(TEST_USER[1]['email'], 'wrong')
    rv = edit_group_item_api(client, 1, creds, description, treffpunkt,
                             treffzeit, zielgruppe)

    assert rv.status_code == 401

    # not own group
    creds = create_api_creds(TEST_USER[1]['email'], TEST_USER[1]['password'])
    rv = edit_group_item_api(client, 1, creds, description, treffpunkt,
                             treffzeit, zielgruppe)

    assert rv.status_code == 401

    # own group
    creds = create_api_creds(TEST_USER[0]['email'], TEST_USER[0]['password'])
    rv = edit_group_item_api(client, 1, creds, description, treffpunkt,
                             treffzeit, zielgruppe)

    assert rv.status_code == 200

    rv_json = json.loads(rv.data)['group']

    assert rv_json['description'] == description
    assert rv_json['treffpunkt'] == treffpunkt
    assert rv_json['treffzeit'] == treffzeit
    assert rv_json['zielgruppe'] == zielgruppe


def test_edit_group_item_avatar(client, image):
    creds = create_api_creds(TEST_USER[0]['email'], TEST_USER[0]['password'])

    rv = get_group_item_api(client, creds, 1)

    assert json.loads(rv.data)['group']['avatar_id'] is None

    # upload image
    rv = edit_group_item_api_avatar(client, 1, creds, image)

    assert json.loads(rv.data)['group']['avatar_id'] is not None


def test_get_profile(client):
    # unauhorized
    rv = client.get('/api/profile/1')

    assert rv.status_code == 401

    # own profile
    test_user = TEST_USER[0]
    creds = create_api_creds(test_user['email'], test_user['password'])

    # non existing profile
    rv = get_profile_api(client, creds, 1)

    assert rv.status_code == 404

    # own profile
    rv = get_profile_api(client, creds, 163)

    assert rv.status_code == 200

    data_dict = json.loads(rv.data)['profile']

    assert data_dict['id'] == test_user['id']
    assert data_dict['name'] == test_user['name'].decode('utf-8')
    assert data_dict['first_name'] == test_user['vorname'].decode('utf-8')
    assert data_dict['street'] == test_user['strasse'].decode('utf-8')
    assert data_dict['postal_code'] == test_user['plz'].decode('utf-8')
    assert data_dict['city'] == test_user['ort'].decode('utf-8')
    assert data_dict['avatar_id'] is None
    assert data_dict['bio'] is None
    assert data_dict['twitter'] is None
    assert data_dict['facebook'] is None


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile(client, test_user, reset_ct_user):
    # fake data
    street = 'fakestreet 1'
    postal_code = '1234'
    city = 'fakecity'
    bio = 'fakebio'
    twitter = 'faketwitter'
    facebook = 'fakefacebook'

    # wrong profile
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = edit_profile_api(client, 1, creds, street, postal_code, city, bio,
                          twitter, facebook)

    # forbidden
    assert rv.status_code == 401

    # own profile
    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = edit_profile_api(client, test_user['id'], creds, street, postal_code,
                          city, bio, twitter, facebook)

    assert rv.status_code == 200

    data_dict = json.loads(rv.data)['profile']

    assert data_dict['id'] == test_user['id']
    assert data_dict['name'] == test_user['name'].decode('utf-8')
    assert data_dict['first_name'] == test_user['vorname'].decode('utf-8')
    assert data_dict['street'] == street
    assert data_dict['postal_code'] == postal_code
    assert data_dict['city'] == city
    assert data_dict['avatar_id'] is None
    assert data_dict['bio'] == bio
    assert data_dict['twitter'] == twitter
    assert data_dict['facebook'] == facebook


@pytest.mark.parametrize('test_user', TEST_USER)
def test_edit_profile_avatar(client, image, test_user):
    creds = create_api_creds(test_user['email'], test_user['password'])

    rv = get_profile_api(client, creds, test_user['id'])

    assert json.loads(rv.data)['profile']['avatar_id'] is None

    # upload file
    rv = edit_profile_api_avatar(client, test_user['id'], creds, image)

    assert json.loads(rv.data)['profile']['avatar_id'] is not None

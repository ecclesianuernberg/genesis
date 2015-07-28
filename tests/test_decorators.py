# -*- coding: utf-8 -*-
from flask.ext.login import login_required
from flask.ext.restful import Resource, Api
from helper import login, create_api_creds, get_auth_api
import app
import json


# get test user
TEST_USER = app.app.config['TEST_USER']


def test_valid_users_and_groups(client):
    @app.app.route('/test')
    @login_required
    @app.auth.valid_groups_and_users(users=[163], groups=[1])
    def view():
        return 'access'

    test_user = TEST_USER[0]

    # not logged in
    rv = client.get('/test')

    assert rv.status_code == 302

    # logged in with valid user
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/test')

    assert rv.status_code == 200
    assert rv.data == 'access'

    # wrong user
    test_user = TEST_USER[1]
    login(client, test_user['email'], test_user['password'])
    rv = client.get('/test')

    assert rv.status_code == 403


def test_valid_users_and_groups_api(client):
    api = Api(app.app)

    class TestAPI(Resource):
        @app.basic_auth.login_required
        @app.auth.valid_groups_and_users(users=[163], groups=[1])
        def get(self):
            return {'return': 'access'}

    api.add_resource(TestAPI, '/api/test')

    # not authorized
    rv = client.get('/api/test')

    assert rv.status_code == 401

    # no valid user
    test_user = TEST_USER[1]

    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_auth_api(client, creds, '/api/test')

    assert rv.status_code == 403

    # valid user
    test_user = TEST_USER[0]

    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_auth_api(client, creds, '/api/test')

    assert rv.status_code == 200
    assert json.loads(rv.data) == {'return': 'access'}

# -*- coding: utf-8 -*-
import pytest

from app import APP, auth
from helper import login, create_api_creds, get_auth_api


# get test user
TEST_USER = APP.config['TEST_USER']


@pytest.mark.parametrize('test_user, status_code', [
    (TEST_USER[0], 200),
    (TEST_USER[1], 401)])
def test_valid_users_and_groups(client, test_user, status_code):
    url = '/test/valid-users-and-groups'

    # not logged in
    rv = client.get(url)

    assert rv.status_code == 302

    login(client, test_user['email'], test_user['password'])
    rv = client.get(url)

    assert rv.status_code == status_code


@pytest.mark.parametrize('test_user, status_code', [
    (TEST_USER[0], 200),
    (TEST_USER[1], 401)])
def test_valid_users_and_groups_api(client, test_user, status_code):
    url = '/test/api/valid-users-and-groups'

    # not authorized
    rv = client.get(url)

    assert rv.status_code == 401

    creds = create_api_creds(test_user['email'], test_user['password'])
    rv = get_auth_api(client, creds, url)

    assert rv.status_code == status_code


@pytest.mark.parametrize('token, status_code', [
    ('wrongtoken', 401),
    (auth.generate_feed_auth(TEST_USER[0]), 200)])
def test_feed_authorized(client, token, status_code):
    url = '/test/feed-authorized'
    rv = client.get(url)

    assert rv.status_code == 401

    rv = client.get('{}?token={}'.format(url, token))

    assert rv.status_code == status_code

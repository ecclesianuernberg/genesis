from flask.ext.login import login_required
from flask.ext.restful import Api, Resource

from app import APP, BASIC_AUTH, auth


API = Api(APP)


@APP.route('/test/feed-authorized')
@auth.feed_authorized
def feed_authorized():
    return 'access'


@APP.route('/test/valid-users-and-groups')
@login_required
@auth.valid_groups_and_users(users=[163], groups=[1])
def valid_users_and_groups():
    return 'access'


class ValidUsersAndGroupsAPI(Resource):
    @BASIC_AUTH.login_required
    @auth.valid_groups_and_users(users=[163], groups=[1])
    def get(self):
        return {'return': 'access'}

API.add_resource(ValidUsersAndGroupsAPI, '/test/api/valid-users-and-groups')

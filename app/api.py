from app import app, api, auth, basic_auth, db, ct_connect, models
from app.views import save_image
from auth import prayer_owner, generate_auth_token, own_group
from datetime import datetime
from flask import jsonify, g, request
from flask.ext.restful import (Resource, reqparse, fields, marshal_with, abort)
from models import get_random_prayer, get_prayer
from unidecode import unidecode
import imghdr
import werkzeug.datastructures


def get_users_name(email):
    person = ct_connect.get_person(email)
    name = '{} {}'.format(unidecode(person.vorname), unidecode(person.name))
    return name


def prayer_fields(endpoint):
    ''' returns dict for using with marshal '''
    return {
        'prayer': fields.String,
        'name': fields.String,
        'id': fields.Integer,
        'pub_date': fields.DateTime,
        'uri': fields.Url(endpoint)
    }


@app.route('/api/token')
@basic_auth.login_required
def get_auth_token():
    token = generate_auth_token(g.user)
    return jsonify({'token': token.decode('ascii')})


class PrayerObject(object):
    def __init__(self, prayer, name, id, pub_date):
        self.prayer = prayer
        self.name = name
        self.id = id
        self.pub_date = pub_date


class PrayerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('body',
                                   type=str,
                                   required=True,
                                   location='json')
        self.reqparse.add_argument('active', type=bool, location='json')
        self.reqparse.add_argument('name', type=str, location='json')

        super(PrayerAPI, self).__init__()

    @basic_auth.login_required
    @marshal_with(prayer_fields('prayerapi'))
    def get(self):
        prayer = get_random_prayer()

        if prayer is None:
            abort(404, message='No Prayers found.')

        return PrayerObject(prayer=prayer.body,
                            name=prayer.name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)

    @basic_auth.login_required
    @marshal_with(prayer_fields('prayerapi'))
    def post(self):
        args = self.reqparse.parse_args()

        # check if user_metadata exists
        user_metadata = models.get_user_metadata(g.user['id'])

        if not user_metadata:
            metadata = models.UserMetadata(g.user['id'])
            db.session.add(metadata)
            db.session.commit()

        prayer = models.Prayer(user_id=g.user['id'],
                               name=args['name'],
                               active=True,
                               pub_date=datetime.utcnow(),
                               body=args['body'])

        db.session.add(prayer)
        db.session.commit()

        return PrayerObject(prayer=prayer.body,
                            name=prayer.name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)


class PrayerAPIEdit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('body', type=str, location='json')
        self.reqparse.add_argument('active', type=bool, location='json')
        self.reqparse.add_argument('name', type=str, location='json')

        super(PrayerAPIEdit, self).__init__()

    @basic_auth.login_required
    @prayer_owner
    @marshal_with(prayer_fields('prayerapiedit'))
    def put(self, id):
        prayer = get_prayer(id)

        args = self.reqparse.parse_args()

        if args['body'] is not None:
            prayer.body = args['body']
        if args['active'] is not None:
            value = args['active']
            prayer.active = value
        if args['name'] is not None:
            prayer.name = args['name']

        db.session.commit()

        return PrayerObject(prayer=prayer.body,
                            name=prayer.name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)

    @basic_auth.login_required
    @prayer_owner
    def delete(self, id):
        prayer = get_prayer(id)

        if prayer:
            db.session.delete(prayer)
            db.session.commit()

            return '', 204
        else:
            abort(404)


group_overview_fields = {
    'name': fields.String,
    'description': fields.String,
    'id': fields.Integer,
    'avatar_id': fields.String,
    'treffzeit': fields.String,
    'treffpunkt': fields.String,
    'zielgruppe': fields.String,
    'notiz': fields.String
}


class GroupOverviewObject(object):
    def __init__(self, ct, metadata, authorized):
        # metadata
        for attribute in ['description, avatar_id']:
            if not hasattr(metadata, attribute) or \
                    metadata.__dict__[attribute] == '':
                self.__dict__[attribute] = None
            else:
                self.__dict__[attribute] = metadata.__dict__[attribute]

        # churchtools
        self.name = ct.bezeichnung.split(' - ')[-1]
        self.id = ct.id

        for attribute in ['treffzeit', 'zielgruppe', 'notiz']:
            if not hasattr(ct, attribute) or ct.__dict__[attribute] == '':
                self.__dict__[attribute] = None
            else:
                self.__dict__[attribute] = ct.__dict__[attribute]

        # treffpunkt just gets returned if user is authorized
        if authorized:
            if not hasattr(ct, 'treffpunkt') or ct.treffpunkt == '':
                self.treffpunkt = None
            else:
                self.treffpunkt = ct.treffpunkt


class GroupAPIOverview(Resource):
    @marshal_with(group_overview_fields, envelope='groups')
    def get(self):
        with ct_connect.session_scope() as ct_session:
            groups = ct_connect.get_active_groups(ct_session)
            groups_metadata = [models.get_group_metadata(i.id) for i in groups]

            authorized = auth.is_basic_authorized()

            group_list = []
            for pos, group in enumerate(groups):
                group_list.append(
                    GroupOverviewObject(ct=group, metadata=groups_metadata[pos],
                                        authorized=authorized))

            return group_list


def group_fields(endpoint):
    return {
        'name': fields.String,
        'id': fields.Integer,
        'description': fields.String,
        'treffzeit': fields.String,
        'treffpunkt': fields.String,
        'zielgruppe': fields.String,
        'notiz': fields.String,
        'avatar_id': fields.String,
        'uri': fields.Url(endpoint)
    }


class GroupObject(object):
    def __init__(self, ct, metadata):
        # this is a pretty ugly hack. even if it still works im not sure what
        # to do with it. i just want to get rid of alot of boilerplate
        # with this. i use this to clean empty strings to None that the API
        # return a NULL instead of a empty string.

        # metadata
        for attribute in ['description', 'avatar_id']:
            if not hasattr(metadata, attribute) or \
                    metadata.__dict__[attribute] == '':
                self.__dict__[attribute] = None
            else:
                self.__dict__[attribute] = metadata.__dict__[attribute]

        # churchtools
        self.name = ct.bezeichnung.split(' - ')[-1]
        self.id = ct.id

        for attribute in ['treffzeit', 'treffpunkt', 'zielgruppe', 'notiz']:
            if not hasattr(ct, attribute) or ct.__dict__[attribute] == '':
                self.__dict__[attribute] = None
            else:
                self.__dict__[attribute] = ct.__dict__[attribute]


class GroupAPIItem(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('description', location='json')
        self.reqparse.add_argument('treffpunkt', location='json')
        self.reqparse.add_argument('treffzeit', location='json')
        self.reqparse.add_argument('zielgruppe', location='json')
        self.reqparse.add_argument(
            'avatar', type=werkzeug.datastructures.FileStorage,
            location='files')

    @basic_auth.login_required
    @marshal_with(group_fields('groupapiitem'), envelope='group')
    def get(self, id):
        with ct_connect.session_scope() as ct_session:
            group = ct_connect.get_group(ct_session, id)
            if not group:
                abort(404)

            group_metadata = models.get_group_metadata(id)

            return GroupObject(ct=group, metadata=group_metadata)

    @basic_auth.login_required
    @own_group
    @marshal_with(group_fields('groupapiitem'), envelope='group')
    def put(self, id):
        args = self.reqparse.parse_args()

        with ct_connect.session_scope() as ct_session:
            group = ct_connect.get_group(ct_session, id)
            if not group:
                abort(404)

            # handling metadata
            group_metadata = models.get_group_metadata(id)

            if not group_metadata:
                group_metadata = models.GroupMetadata(ct_id=id)
                db.session.add(group_metadata)

            if args['description'] is not None:
                group_metadata.description = args['description']

            # handling the avatar upload
            if args['avatar'] is not None:

                # needs to be a jpeg else rise a "unsupported" media type error
                if imghdr.what(args['avatar']) != 'jpeg':
                    abort(415, message='Nur JPGs')

                group_image = save_image(
                    args['avatar'], request_path=request.path,
                    user_id=g.user['id'])

                group_metadata.avatar_id = group_image

            # handling ct data
            if args['treffpunkt'] is not None:
                group.treffpunkt = args['treffpunkt']

            if args['treffzeit'] is not None:
                group.treffzeit = args['treffzeit']

            if args['zielgruppe'] is not None:
                group.zielgruppe = args['zielgruppe']

            # saving everything
            db.session.commit()
            ct_session.add(group)
            ct_session.commit()

            return GroupObject(ct=ct_connect.get_group(ct_session, id),
                               metadata=models.get_group_metadata(id))


def profile_fields(endpoint):
    return {
        'id': fields.Integer,
        'first_name': fields.String,
        'name': fields.String,
        'street': fields.String,
        'postal_code': fields.String,
        'city': fields.String,
        'avatar': fields.String,
        'bio': fields.String,
        'twitter': fields.String,
        'facebook': fields.String,
        'uri': fields.Url(endpoint)
    }


class ProfileObject(object):
    def __init__(self, id, first_name, name, street, postal_code, city, avatar,
                 bio, twitter, facebook):
        self.id = id
        self.first_name = first_name
        self.name = name
        self.street = street
        self.city = city
        self.avatar = avatar
        self.bio = bio
        self.twitter = twitter
        self.facebook = facebook


class ProfileAPI(Resource):
    @basic_auth.login_required
    @marshal_with(profile_fields('profileapi'), envelope='profile')
    def get(self, id):
        with ct_connect.session_scope() as ct_session:
            user = ct_connect.get_person_from_id(ct_session, id)
            if not user:
                abort(404)

            user = user[0]

            # getting metadata
            user_metadata = models.get_user_metadata(id)

            own_profile = False
            if g.user['id'] == id:
                own_profile = True

            # avatar
            if not hasattr(user_metadata, 'avatar_id') or \
                    user_metadata.avatar_id == '':
                avatar = None
            else:
                avatar = user_metadata.avatar_id

            # bio
            if not hasattr(user_metadata, 'bio') or \
                    user_metadata.bio == '':
                bio = None
            else:
                bio = user_metadata.bio

            # twitter
            if not hasattr(user_metadata, 'twitter') or \
                    user_metadata.twitter == '':
                twitter = None
            else:
                twitter = user_metadata.twitter

            # facebook
            if not hasattr(user_metadata, 'facebook') or \
                    user_metadata.facebook == '':
                facebook = None
            else:
                facebook = user_metadata.facebook

            return ProfileObject(user.id, user.vorname, user.name,
                                 user.strasse, user.plz, user.ort, avatar, bio,
                                 twitter, facebook)


api.add_resource(PrayerAPI, '/api/prayer')
api.add_resource(PrayerAPIEdit, '/api/prayer/<int:id>')
api.add_resource(GroupAPIOverview, '/api/groups')
api.add_resource(GroupAPIItem, '/api/group/<int:id>')
api.add_resource(ProfileAPI, '/api/profile/<int:id>')

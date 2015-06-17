from app import app, api, auth, basic_auth, db, ct_connect, models
from datetime import datetime
from flask import jsonify, g
from flask.ext.restful import (Resource, reqparse, fields, marshal_with, abort)
from unidecode import unidecode
from models import get_random_prayer, get_prayer
from auth import prayer_owner, generate_auth_token


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
    'avatar': fields.String,
    'treffzeit': fields.String,
    'treffpunkt': fields.String,
    'zielgruppe': fields.String,
    'notiz': fields.String
}


class GroupOverviewObject(object):
    def __init__(self, name, description, id, avatar, treffzeit, treffpunkt,
                 zielgruppe, notiz):
        self.name = name
        self.description = description
        self.id = id
        self.avatar = avatar
        self.treffzeit = treffzeit
        self.treffpunkt = treffpunkt
        self.zielgruppe = zielgruppe
        self.notiz = notiz


class GroupAPIOverview(Resource):
    @marshal_with(group_overview_fields)
    def get(self):
        print auth.is_basic_authorized()
        with ct_connect.session_scope() as ct_session:
            groups = ct_connect.get_active_groups(ct_session)
            groups_metadata = [models.get_group_metadata(i.id) for i in groups]

            authorized = auth.is_basic_authorized()

            group_list = []
            for id, group in enumerate(groups):

                # description
                if hasattr(groups_metadata[id], 'description'):
                    description = groups_metadata[id].description
                else:
                    description = ''

                # avatar
                if hasattr(groups_metadata[id], 'avatar_id'):
                    avatar_id = groups_metadata[id].avatar_id
                else:
                    avatar_id = ''

                # treffpunkt
                if authorized:
                    treffpunkt = group.treffpunkt
                else:
                    treffpunkt = ''

                name = group.bezeichnung.split(' - ')[-1]

                group_list.append(
                    GroupOverviewObject(name, description, group.id, avatar_id,
                                        group.treffzeit, treffpunkt,
                                        group.zielgruppe, group.notiz))

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
        'avatar': fields.String,
        'uri': fields.Url(endpoint)
    }


class GroupObject(object):
    def __init__(self, name, id, description, treffzeit, treffpunkt,
                 zielgruppe, notiz, avatar):
        self.name = name
        self.id = id
        self.description = description
        self.treffzeit = treffzeit
        self.treffpunkt = treffpunkt
        self.zielgruppe = zielgruppe
        self.notiz = notiz
        self.avatar = avatar


class GroupAPIItem(Resource):
    @basic_auth.login_required
    @marshal_with(group_fields('groupapiitem'))
    def get(self, id):
        with ct_connect.session_scope() as ct_session:
            group = ct_connect.get_group(ct_session, id)
            if not group:
                abort(404)

            group_metadata = models.get_group_metadata(id)

            name = group.bezeichnung.split(' - ')[-1]

            if hasattr(group_metadata, 'description'):
                description = group_metadata.description
            else:
                description = ''

            if hasattr(group_metadata, 'avatar_id'):
                avatar = group_metadata.avatar_id
            else:
                avatar = ''

            return GroupObject(name, group.id, description, group.treffzeit,
                               group.treffpunkt, group.zielgruppe, group.notiz,
                               avatar)


api.add_resource(PrayerAPI, '/api/prayer')
api.add_resource(PrayerAPIEdit, '/api/prayer/<int:id>')
api.add_resource(GroupAPIOverview, '/api/groups')
api.add_resource(GroupAPIItem, '/api/group/<int:id>')

from app import app, api, basic_auth, db
from datetime import datetime
from flask import jsonify, g
from flask.ext.restful import (
    Resource,
    reqparse,
    fields,
    marshal_with,
    abort)
from unidecode import unidecode
from . import (
    ct_connect,
    models)
from views import get_random_prayer, get_prayer
from auth import prayer_owner_or_403


def get_users_name(email):
    person = ct_connect.get_person(email)
    name = '{} {}'.format(
        unidecode(person.vorname),
        unidecode(person.name))
    return name


def create_prayer_fields(endpoint):
    ''' returns dict for using with marshal '''
    return {
        'prayer': fields.String,
        'name': fields.String,
        'id': fields.Integer,
        'pub_date': fields.DateTime,
        'uri': fields.Url(endpoint)}


@app.route('/api/token')
@basic_auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
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
        self.reqparse.add_argument(
            'body',
            type=str,
            required=True,
            location='json')
        self.reqparse.add_argument(
            'active',
            type=bool,
            location='json')
        self.reqparse.add_argument(
            'show_user',
            type=bool,
            location='json')

        super(PrayerAPI, self).__init__()

    @basic_auth.login_required
    @marshal_with(create_prayer_fields('prayerapi'))
    def get(self):
        prayer = get_random_prayer()
        if prayer.show_user:
            name = get_users_name(prayer.user)
        else:
            name = 'anonym'

        return PrayerObject(prayer=prayer.body,
                            name=name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)

    @basic_auth.login_required
    @marshal_with(create_prayer_fields('prayerapi'))
    def post(self):
        args = self.reqparse.parse_args()
        prayer = models.Prayer(
            user=g.user.id,
            show_user=args['show_user'],
            active=True,
            pub_date=datetime.utcnow(),
            body=args['body'])
        db.session.add(prayer)
        db.session.commit()

        if prayer.show_user:
            name = get_users_name(prayer.user)
        else:
            name = 'anonym'

        return PrayerObject(prayer=prayer.body,
                            name=name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)


class PrayerAPIEdit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'body',
            type=str,
            location='json')
        self.reqparse.add_argument(
            'active',
            type=bool,
            location='json')
        self.reqparse.add_argument(
            'show_user',
            type=bool,
            location='json')

        super(PrayerAPIEdit, self).__init__()

    @basic_auth.login_required
    @marshal_with(create_prayer_fields('prayerapiedit'))
    def put(self, id):
        prayer_owner_or_403(id)

        prayer = get_prayer(id)

        args = self.reqparse.parse_args()

        if args['body'] is not None:
            prayer.body = args['body']
        if args['active'] is not None:
            value = args['active']
            prayer.active = value
        if args['show_user'] is not None:
            prayer.show_user = args['show_user']

        db.session.commit()

        if prayer.show_user:
            name = get_users_name(prayer.user)
        else:
            name = 'anonym'

        return PrayerObject(prayer=prayer.body,
                            name=name,
                            id=prayer.id,
                            pub_date=prayer.pub_date)

    @basic_auth.login_required
    def delete(self, id):
        prayer = get_prayer(id)

        if prayer:
            prayer_owner_or_403(id)
            db.session.delete(prayer)
            db.session.commit()

            return '', 204
        else:
            abort(404)


api.add_resource(
    PrayerAPI,
    '/api/prayer')

api.add_resource(
    PrayerAPIEdit,
    '/api/prayer/<int:id>')

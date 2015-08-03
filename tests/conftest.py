import pytest
import tempfile
import shutil
from PIL import Image
from passlib.hash import bcrypt

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

os.environ['FLASK_CONFIG'] = 'testing'

from app import APP, DB, ct_connect


# get test user
TEST_USER = APP.config['TEST_USER']


@pytest.yield_fixture
def db():
    ''' creates tables and drops them for every test '''
    DB.create_all()

    yield

    DB.session.commit()
    DB.drop_all()


@pytest.yield_fixture
def client(db):
    # create temp upload folder
    upload_dir = tempfile.mkdtemp()
    APP.config['UPLOAD_FOLDER'] = upload_dir

    yield APP.test_client()

    # delete temp upload folder
    shutil.rmtree(upload_dir)


@pytest.yield_fixture
def image():
    ''' creates temp image '''
    img = Image.new('RGB', (1000, 1000))
    temp_file = '{}.jpg'.format(tempfile.mktemp())
    img.save(temp_file)

    yield temp_file

    os.remove(temp_file)


@pytest.fixture
def reset_ct_user(request):
    ''' reset ct user db entries '''
    with ct_connect.session_scope() as ct_session:
        # getting ids from the test user
        test_ids = [i['id'] for i in TEST_USER]

        # list of test user db entries
        ct_entries = [ct_connect.get_person_from_id(ct_session, i)[0]
                      for i in test_ids]

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
                user = ct_connect.get_person_from_id(ct_session,
                                                     entry['id'])[0]
                user.strasse = entry['strasse']
                user.plz = entry['plz']
                user.ort = entry['ort']
                user.password = entry['password']

                # save to db
                ct_session.add(user)

            ct_session.commit()

        request.addfinalizer(fin)
        return True


@pytest.fixture
def reset_ct_group(request):
    ''' reset test group data in db '''
    with ct_connect.session_scope() as ct_session:
        # getting group out of churchtools db
        group = ct_connect.get_group(ct_session, 1)

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
            ct_session.add(group)
            ct_session.commit()

        request.addfinalizer(fin)


def ct_create_person(user_data):
    ''' creates temp churchtools person '''
    with ct_connect.session_scope() as ct_session:
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
            ct_session.add(temp_user)

        # save to db
        ct_session.commit()


def ct_delete_person(user_data):
    with ct_connect.session_scope() as ct_session:
        # for each user in user_data find and delete entry
        for user in user_data:
            ct_session.query(ct_connect.Person).filter(
                ct_connect.Person.email == user['email'],
                ct_connect.Person.name == user['name'],
                ct_connect.Person.vorname == user['vorname']).delete()

        # save to db
        ct_session.commit()


@pytest.fixture
def ct_same_username_and_password(request):
    user_data = [{
        'email': 'test@test.com',
        'password': 'testpassword',
        'vorname': 'Testvorname',
        'name': 'Testnachname'
    }, {
        'email': 'test@test.com',
        'password': 'testpassword',
        'vorname': 'AnotherTestvorname',
        'name': 'AnotherTestnachname'
    }]

    ct_create_person(user_data)

    def fin():
        ct_delete_person(user_data)

    request.addfinalizer(fin)
    return user_data


@pytest.yield_fixture
def clean_whoosh_index():
    whoosh_base = tempfile.mkdtemp()
    APP.config['WHOOSH_BASE'] = whoosh_base

    yield

    shutil.rmtree(whoosh_base)

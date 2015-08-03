# -*- coding: utf-8 -*-
import pytest
from app import APP, ct_connect
from datetime import datetime
from passlib.hash import bcrypt


# get test user
TEST_USER = APP.config['TEST_USER']


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_get_person(test_user):
    ''' person out of churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_person(ct_session, test_user['email'])

        assert test_user['name'] in [i.name for i in rv]
        assert test_user['vorname'] in [i.vorname for i in rv]


@pytest.mark.parametrize('test_user', TEST_USER[1:3])
def test_person_from_id(test_user):
    ''' person out of churchtools from id '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_person_from_id(ct_session, test_user['id'])[0]

        assert rv.email == test_user['email']
        assert rv.name == test_user['name']
        assert rv.vorname == test_user['vorname']


def test_get_active_groups():
    ''' list of active groups out of churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_active_groups(ct_session)

        assert u'KG - Test' in [i.bezeichnung for i in rv]


def test_get_group():
    ''' specific group out of churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_group(ct_session, 1)

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


def test_get_group_heads():
    ''' list of group heads out of churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_group_heads(ct_session, 1)

        assert [u'Leiter', u'Preuß'] == [i.name for i in rv]


def test_get_group_members():
    ''' group members out of churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_group_members(ct_session, 1)

        assert [118, 163, 383] == [i.id for i in rv]


def test_get_person_from_communityperson():
    ''' person object out of communityperson from churchtools '''
    with ct_connect.session_scope() as ct_session:
        rv = ct_connect.get_person_from_communityperson(ct_session, 118)

        assert rv.name == u'Leiter'
        assert rv.vorname == u'Test'
        assert rv.email == u'test.leiter@ecclesianuernberg.de'


@pytest.mark.parametrize('test_user', TEST_USER)
def test_change_user_password(test_user):
    ''' change user password in churchtools '''
    with ct_connect.session_scope() as ct_session:
        # check if test_user password is the one in the churchtools-db
        db_user = ct_connect.get_person_from_id(ct_session, test_user['id'])[0]

        assert bcrypt.verify(test_user['password'], db_user.password)

        # new password
        password = 'newpassword'
        ct_connect.change_user_password(ct_session, test_user['id'], password)
        db_user = ct_connect.get_person_from_id(ct_session, test_user['id'])[0]

        assert bcrypt.verify(password, db_user.password)

        # reset password
        ct_connect.change_user_password(ct_session, test_user['id'],
                                        test_user['password'])

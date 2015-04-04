from app import app
from sqlalchemy import (
    create_engine,
    MetaData,
    Table)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.hash import bcrypt


URI = app.config['SQLALCHEMY_CT_DATABASE_URI']
BASE = declarative_base()
ENGINE = create_engine(URI, echo=False, pool_recycle=3600)
METADATA = MetaData(bind=ENGINE)
Session = sessionmaker(bind=ENGINE)
SESSION = Session()


class Person(BASE):
    __table__ = Table(
        'DruInt_cdb_person',
        METADATA,
        autoload=True)


class Group(BASE):
    __table__ = Table(
        'DruInt_cdb_gruppe',
        METADATA,
        autoload=True)


class CommunityPerson(BASE):
    __table__ = Table(
        'DruInt_cdb_gemeindeperson',
        METADATA,
        autoload=True)


class CommunityPersonInGroup(BASE):
    __table__ = Table(
        'DruInt_cdb_gemeindeperson_gruppe',
        METADATA,
        autoload=True)


class GroupMemberStatus(BASE):
    __table__ = Table(
        'DruInt_cdb_gruppenteilnehmerstatus',
        METADATA,
        autoload=True)


def get_person(email):
    return SESSION.query(
        Person).filter(
            Person.email == email).all()


def get_person_from_id(id):
    return SESSION.query(
        Person).filter(
            Person.id == id).all()


def get_active_groups():
    return SESSION.query(Group).filter(
        Group.gruppentyp_id == '1',
        Group.abschlussdatum == None,
        Group.versteckt_yn == '0').all()


def get_group(id):
    return SESSION.query(Group).filter(
        Group.id == id).first()


def get_group_heads(id):
    head_list = []
    heads = SESSION.query(CommunityPersonInGroup).filter(
        CommunityPersonInGroup.gruppe_id == id,
        CommunityPersonInGroup.status_no == 1).all()
    for head in heads:
        head_list.append(
            get_person_from_communityperson(head.gemeindeperson_id))

    return head_list


def get_group_members(id):
    return SESSION.query(CommunityPerson).join(
        CommunityPersonInGroup,
        CommunityPerson.id == CommunityPersonInGroup.gemeindeperson_id).filter(
            CommunityPersonInGroup.gruppe_id == id).all()


def get_person_from_communityperson(id):
    return SESSION.query(Person).join(
        CommunityPerson,
        Person.id == CommunityPerson.person_id).filter(
            CommunityPerson.person_id == id).first()


def change_user_password(id, password):
    user = get_person_from_id(id)[0]
    user.password = bcrypt.encrypt(password)
    SESSION.add(user)
    SESSION.commit()

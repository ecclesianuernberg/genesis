"""Connection to churchtools."""

from sqlalchemy import (create_engine, MetaData, Table, exc, event, or_, and_)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from passlib.hash import bcrypt

from app import APP


URI = APP.config['SQLALCHEMY_CT_DATABASE_URI']
BASE = declarative_base()
ENGINE = create_engine(URI, echo=False, pool_recycle=3600)
METADATA = MetaData(bind=ENGINE)
SESSION = sessionmaker(bind=ENGINE)


@contextmanager
def session_scope():
    """Context for using a churchtools session."""
    session = SESSION()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@event.listens_for(Pool, 'checkout')
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """Pings connection and raise disconnect error if it cants execute
    a select.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute('SELECT 1')
    except:
        raise exc.DisconnectError()
    cursor.close()


class Person(BASE):
    """Churchtools person table."""
    __table__ = Table('DruInt_cdb_person', METADATA, autoload=True)


class Group(BASE):
    """Churchtools gruppe table."""
    __table__ = Table('DruInt_cdb_gruppe', METADATA, autoload=True)


class CommunityPerson(BASE):
    """Churchtools gemeindeperson table."""
    __table__ = Table('DruInt_cdb_gemeindeperson', METADATA, autoload=True)


class CommunityPersonInGroup(BASE):
    """Churchtools gemeindeperson gruppe table."""
    __table__ = Table('DruInt_cdb_gemeindeperson_gruppe', METADATA,
                      autoload=True)


class GroupMemberStatus(BASE):
    """Churchtools gruppenteilnehmerstatus table."""
    __table__ = Table('DruInt_cdb_gruppenteilnehmerstatus', METADATA,
                      autoload=True)


def get_person(session, email):
    """Return churchtools person from email adress."""
    return session.query(Person).filter(Person.email == email).all()


def get_person_from_id(session, id):
    """Return churchtools person from id."""
    return session.query(Person).filter(Person.id == id).all()


def get_active_groups(session):
    """Return active churchtools kleingruppen."""
    return session.query(Group).filter(Group.gruppentyp_id == '1',
                                       Group.abschlussdatum == None,
                                       Group.versteckt_yn == '0').all()


def get_group(session, id):
    """Return churchtools kleingruppe from id."""
    return session.query(Group).filter(Group.id == id).first()


def get_group_heads(session, id):
    """Return list of churchtools kleingruppenleiter from id."""
    head_list = []
    heads = session.query(CommunityPersonInGroup).filter(
        CommunityPersonInGroup.gruppe_id == id,
        CommunityPersonInGroup.status_no == 1).all()
    for head in heads:
        head_list.append(
            get_person_from_communityperson(session, head.gemeindeperson_id))

    return head_list


def get_group_members(session, id):
    """Return churchtools kleingruppen members."""
    return session.query(CommunityPerson).join(
        CommunityPersonInGroup,
        CommunityPerson.id == CommunityPersonInGroup.gemeindeperson_id).filter(
            CommunityPersonInGroup.gruppe_id == id).all()


def get_person_from_communityperson(session, id):
    """Return churchtools person from gemeindeperson id."""
    return session.query(Person).join(
        CommunityPerson, Person.id == CommunityPerson.person_id).filter(
            CommunityPerson.person_id == id).first()


def change_user_password(session, id, password):
    """Change churchtools user password."""
    user = get_person_from_id(session, id)[0]
    user.password = bcrypt.encrypt(password)
    session.add(user)
    session.commit()


def search_person(session, query):
    """Return a list of users for searching."""
    # split the query in list of words
    query = query.split(' ')

    user = []

    # if there is only one string in list check if its vorname or name
    if len(query) == 1:
        user.extend(session.query(Person).filter(
            or_(Person.vorname == query[0].title(),
                Person.name == query[0].title())).all())

    # check for the full name
    else:
        user.extend(session.query(Person).filter(
            and_(Person.vorname == query[0].title(),
                 Person.name == query[1].title())).all())

    return user

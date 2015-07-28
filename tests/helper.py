from app import ct_connect
from random import choice
import base64
import json
import app


# get test user
TEST_USER = app.app.config['TEST_USER']


def get_wrong_user_id(own_id):
    ''' returns a id that is not own id '''
    ids = [i['id'] for i in TEST_USER]
    ids.remove(own_id)

    return choice(ids)


def login(client, email, password):
    ''' helper function to login '''
    return client.post('/login',
                       data={'email': email,
                             'password': password},
                       follow_redirects=True)


def logout(client):
    ''' helper function to logout '''
    return client.get('/logout', follow_redirects=True)


def add_prayer(client, body, name=''):
    ''' helper to add a new prayer '''
    return client.post('/prayer/add',
                       data={'body': body,
                             'active': True,
                             'name': name},
                       follow_redirects=True)


def edit_prayer(client, id, body, active=False, name=''):
    ''' helper to edit a prayer '''
    # i discovered some strange behaviour or it was just my head that got
    # twisted. just sending body data it means that the booleanfields are
    # not toggled at all. i could send something like "active: True" or even
    # "active: 'foo" to get a booleanfield data sent to the form. and now
    # even more bizarr: you can send "active: False" and it returns in a True.
    if active:
        return client.post('/prayer/mine',
                           data={
                               '{}-body'.format(id): body,
                               '{}-active'.format(id): True,
                               '{}-name'.format(id): name
                           },
                           follow_redirects=True)

    else:
        return client.post(
            '/prayer/mine',
            data={'{}-body'.format(id): body,
                  '{}-name'.format(id): name},
            follow_redirects=True)


def del_prayer(client, id):
    ''' helper to delete a prayer '''
    return client.get('/prayer/{}/del'.format(id), follow_redirects=True)


def edit_group(client, id, description, where, when, audience, image):
    ''' helper to edit group '''
    with open(image) as f:
        return client.post('/group/{}'.format(id),
                           data={
                               'description': description,
                               'group_image': (f, 'test.jpg'),
                               'where': where,
                               'when': when,
                               'audience': audience},
                           follow_redirects=True)


def create_api_creds(username, password):
    ''' helper to create creds for api usage '''
    user_password = b'{}:{}'.format(username, password)

    return base64.b64encode(user_password).decode('utf-8').strip('\r\n')


def get_api_token(client, creds):
    return client.get('/api/token',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def add_prayer_api(client, body, creds, name=''):
    ''' helper to add a new prayer '''
    return client.post(
        '/api/prayer',
        headers={'Authorization': 'Basic ' + creds},
        data=json.dumps({'body': body,
                         'active': True,
                         'name': name}),
        content_type='application/json')


def edit_prayer_api(client, id, body, creds, active, name=''):
    ''' helper to add a new prayer '''
    return client.put(
        '/api/prayer/{}'.format(id),
        headers={'Authorization': 'Basic ' + creds},
        data=json.dumps({'body': body,
                         'active': active,
                         'name': name}),
        content_type='application/json')


def del_prayer_api(client, id, creds):
    ''' helper to delete prayer '''
    return client.delete('/api/prayer/{}'.format(id),
                         headers={'Authorization': 'Basic ' + creds},
                         content_type='application/json')


def get_prayer_api(client, creds):
    ''' helper to get random prayer '''
    return client.get('/api/prayer',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def edit_profile(client, id, street, postal_code, city, bio, password, twitter,
                 facebook, image):
    with open(image) as f:
        return client.post('/profile/{}'.format(id),
                           data={
                               'street': street,
                               'postal_code': postal_code,
                               'city': city,
                               'bio': bio,
                               'twitter': twitter,
                               'facebook': facebook,
                               'password': password,
                               'confirm': password,
                               'user_image': (f, 'test.jpg')},
                           follow_redirects=True)


def send_mail(client, url, subject, body):
    return client.post(url,
                       data={'subject': subject,
                             'body': body},
                       follow_redirects=True)


def add_whatsup_post(client, subject, body, url='/whatsup'):
    return client.post(url,
                       data={'subject': subject,
                             'body': body},
                       follow_redirects=True)


def add_whatsup_upvote(client, id):
    return client.get('/whatsup/{}/upvote'.format(id), follow_redirects=True)


def add_whatsup_comment(client, id, body):
    return client.post('/whatsup/{}'.format(id),
                       data={'body': body},
                       follow_redirects=True)


def edit_whatsup_post(client, id, subject, body):
    return client.post(
        '/whatsup/mine',
        data={'{}-subject'.format(id): subject,
              '{}-body'.format(id): body},
        follow_redirects=True)


def get_whatsup_feed_posts(client, token):
    return client.get('/feeds/whatsup.atom?token={}'.format(token))


def get_whatsup_feed_comments(client, token):
    return client.get('/feeds/whatsup-comments.atom?token={}'.format(token))


def edit_index(client, image, first_row_link, second_row_link,
               third_row_left_link, third_row_right_link):
    return client.post('/edit',
                       data={
                           'first_row_link': first_row_link,
                           'first_row_image': (open(image), '1.jpg'),
                           'second_row_link': second_row_link,
                           'second_row_image': (open(image), '2.jpg'),
                           'third_row_left_link': third_row_left_link,
                           'third_row_left_image': (open(image), '3.jpg'),
                           'third_row_right_link': third_row_right_link,
                           'third_row_right_image': (open(image), '4.jpg')
                       },
                       follow_redirects=True)


def get_own_group_ids(id):
    with ct_connect.session_scope() as ct_session:
        return [i.id for i in ct_connect.get_active_groups(ct_session) for j in
                ct_connect.get_group_heads(ct_session, i.id) if j.id == id]


def get_other_group_ids(id):
    with ct_connect.session_scope() as ct_session:
        return [i.id for i in ct_connect.get_active_groups(ct_session)
                if id not in [j.id for j in
                              ct_connect.get_group_heads(ct_session, i.id)]]


def search(client, query):
    return client.post('/search',
                       data={'search': query},
                       follow_redirects=True)


def get_group_overview_api(client, creds):
    ''' helper to get group overview over api '''
    return client.get('/api/groups',
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def get_group_item_api(client, creds, id):
    ''' helper to get group over api '''
    return client.get('/api/group/{}'.format(id),
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def edit_group_item_api(client, id, creds, description, treffpunkt, treffzeit,
                        zielgruppe):
    ''' helper to edit group over api '''
    return client.put('/api/group/{}'.format(id),
                      headers={'Authorization': 'Basic ' + creds},
                      data=json.dumps({'description': description,
                                       'treffpunkt': treffpunkt,
                                       'treffzeit': treffzeit,
                                       'zielgruppe': zielgruppe}),
                      content_type='application/json')


def edit_group_item_api_avatar(client, id, creds, image):
    ''' upload group avatar through api '''
    with open(image) as f:
        return client.put('/api/group/{}'.format(id),
                          headers={'Authorization': 'Basic ' + creds},
                          data={'avatar': (f, 'test.jpg')})


def get_profile_api(client, creds, id):
    return client.get('/api/profile/{}'.format(id),
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')


def edit_profile_api(client, id, creds, street, postal_code, city, bio, twitter,
                     facebook):
    return client.put('/api/profile/{}'.format(id),
                      headers={'Authorization': 'Basic ' + creds},
                      data=json.dumps({'street': street,
                                       'postal_code': postal_code,
                                       'city': city,
                                       'bio': bio,
                                       'twitter': twitter,
                                       'facebook': facebook}),
                      content_type='application/json')


def edit_profile_api_avatar(client, id, creds, image):
    ''' upload profile avatar through api '''
    with open(image) as f:
        return client.put('/api/profile/{}'.format(id),
                          headers={'Authorization': 'Basic ' + creds},
                          data={'avatar': (f, 'test.jpg')})


def get_auth_api(client, creds, resource):
    return client.get(resource,
                      headers={'Authorization': 'Basic ' + creds},
                      content_type='application/json')

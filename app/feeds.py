# -*- coding: utf-8 -*-
from app import app, models, basic_auth
from app.views import make_external
from flask import request
from werkzeug.contrib.atom import AtomFeed
from unidecode import unidecode


@app.route('/feeds/whatsup.atom')
@basic_auth.login_required
def whatsup_recent_posts():
    feed = AtomFeed('Recent WhatsUp Posts',
                    feed_url=request.url, url=request.url_root)

    posts = models.get_latest_whatsup_posts(15)

    for post in posts:
        feed.add(post.subject,
                 unicode(post.body),
                 content_type='text',
                 author='{} {}'.format(unidecode(post.user.ct_data.vorname),
                                       unidecode(post.user.ct_data.name)),
                 url=make_external('/whatsup/{}'.format(post.id)),
                 updated=post.pub_date)

    return feed.get_response()


@app.route('/feeds/whatsup-comments.atom')
@basic_auth.login_required
def whatsup_recent_comments():
    feed = AtomFeed('Recent WhatsUp Comments',
                    feed_url=request.url, url=request.url_root)

    comments = models.get_latest_whatsup_comments(15)

    for comment in comments:
        feed.add(
            'Kommentar fuer "{}" von {} {}'.format(
                comment.post.subject,
                unidecode(comment.user.ct_data.vorname),
                unidecode(comment.user.ct_data.name)),
            unicode(comment.body),
            content_type='text',
            author='{} {}'.format(
                unidecode(comment.user.ct_data.vorname),
                unidecode(comment.user.ct_data.name)),
            url=make_external('whatsup/{}#comment{}'.format(
                comment.post.id,
                comment.id)),
            updated=comment.pub_date)

    return feed.get_response()

from app import APP, MAIL
from flask import render_template
from flask_mail import Message


def send_email(subject, sender, recipients, body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = render_template('mail_signature.txt',
                               name=APP.config['NAME'],
                               body=body)
    MAIL.send(msg)

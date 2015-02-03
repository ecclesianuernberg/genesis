from app import app, mail
from flask import render_template
from flask_mail import Message


def send_email(subject, sender, recipients, body):
    msg = Message(subject,
                  sender=sender,
                  recipients=recipients)
    msg.body = render_template('mail_signature.txt',
                               name=app.config['NAME'],
                               body=body)
    mail.send(msg)

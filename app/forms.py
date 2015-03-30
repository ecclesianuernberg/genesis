from flask_wtf import Form
from flask_wtf.file import (
    FileField,
    FileAllowed)
from wtforms import (
    BooleanField,
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField)
import wtforms.validators as validators
from flask.ext.pagedown.fields import PageDownField


class LoginForm(Form):
    email = StringField(
        'Email',
        validators=[validators.DataRequired(),
                    validators.Email()])
    password = PasswordField(
        'Password',
        validators=[validators.DataRequired()])

    submit = SubmitField('Login')


class EditGroupForm(Form):
    # churchtools
    where = StringField('Treffpunkt')
    when = StringField('Treffzeit')
    audience = StringField('Zielgruppe')

    # metadata
    description = PageDownField('Beschreibung',
                                validators=[validators.Length(max=700)])
    group_image = FileField(
        'Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    # submit
    submit = SubmitField('Submit')


class EditIndexForm(Form):
    first_row_image = FileField(
        'Erste Reihe Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    first_row_link = StringField(
        'Erste Reihe Link',
        validators=[validators.URL(require_tld=True)])

    second_row_image = FileField(
        'Zweite Reihe Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    second_row_link = StringField(
        'Zweite Reihe Link',
        validators=[validators.URL(require_tld=True)])

    third_row_left_image = FileField(
        'Dritte Reihe Links Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    third_row_left_link = StringField(
        'Dritte Reihe Links Link',
        validators=[validators.URL(require_tld=True)])

    third_row_right_image = FileField(
        'Dritte Reihe Rechts Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    third_row_right_link = StringField(
        'Dritte Reihe Rechts Link',
        validators=[validators.URL(require_tld=True)])

    # submit
    submit = SubmitField('Submit')


class AddPrayerForm(Form):
    body = PageDownField(
        '',
        validators=[validators.DataRequired(), validators.Length(max=700)])

    show_user = BooleanField('Name anzeigen')

    active = BooleanField('Aktiv')

    submit = SubmitField('Submit')


class EditProfileForm(Form):
    # churchtools
    password = PasswordField(
        'Neues Password',
        validators=[validators.EqualTo('confirm')])

    confirm = PasswordField(
        'Confirm Password')

    street = StringField('Strasse')

    postal_code = StringField('PLZ')

    city = StringField('Ort')

    # metadata
    bio = PageDownField('Bio',
                        validators=[validators.Length(max=700)])

    user_image = FileField(
        'Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])

    twitter = StringField(
        'Twitter',
        validators=[validators.optional(), validators.URL()])

    facebook = StringField(
        'Facebook',
        validators=[validators.optional(), validators.URL()])

    # submit
    submit = SubmitField('Submit')


class MailForm(Form):
    subject = StringField(
        'Betreff',
        validators=[validators.DataRequired()])

    body = TextAreaField(
        'Nachricht',
        validators=[validators.DataRequired()])

    submit = SubmitField('Submit')


class AddWhatsUp(Form):
    subject = StringField('Subject',
                          validators=[validators.DataRequired(),
                                      validators.Length(max=120)])

    body = TextAreaField('Body',
                         validators=[validators.DataRequired(),
                                     validators.Length(max=700)])

    submit = SubmitField('Submit')


class AddWhatsUpComment(Form):
    body = TextAreaField('Kommentar',
                         validators=[validators.DataRequired(),
                                     validators.Length(max=700)])

    submit = SubmitField('Submit')

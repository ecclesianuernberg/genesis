from flask_wtf import Form
from flask_wtf.file import (
    FileField,
    FileAllowed)
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SubmitField)
import wtforms.validators as validators


class EditGroupForm(Form):
    name = StringField(
        'Name',
        validators=[validators.DataRequired()])
    where = StringField(
        'Wo',
        validators=[validators.DataRequired()])
    when = StringField(
        'Wann',
        validators=[validators.DataRequired()])
    short_description = StringField(
        'Kurze Beschreibung',
        validators=[validators.DataRequired()])
    long_description = TextAreaField(
        'Lange Beschreibung',
        validators=[validators.DataRequired()])
    group_image = FileField(
        'Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs')])
    active = BooleanField('Active')
    submit = SubmitField('Submit')


class EditIndexForm(Form):
    first_row_image = FileField(
        'Erste Reihe Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs'),
                    validators.DataRequired()])
    first_row_link = StringField(
        'Erste Reihe Link',
        validators=[validators.DataRequired(),
                    validators.URL(require_tld=True)])
    second_row_image = FileField(
        'Zweite Reihe Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs'),
                    validators.DataRequired()])
    second_row_link = StringField(
        'Zweite Reihe Link',
        validators=[validators.DataRequired(),
                    validators.URL(require_tld=True)])
    third_row_left_image = FileField(
        'Dritte Reihe Links Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs'),
                    validators.DataRequired()])
    third_row_left_link = StringField(
        'Dritte Reihe Links Link',
        validators=[validators.DataRequired(),
                    validators.URL(require_tld=True)])
    third_row_right_image = FileField(
        'Dritte Reihe Rechts Bild',
        validators=[FileAllowed(['jpg'], 'Nur JPGs'),
                    validators.DataRequired()])
    third_row_right_link = StringField(
        'Dritte Reihe Rechts Link',
        validators=[validators.DataRequired(),
                    validators.URL(require_tld=True)])

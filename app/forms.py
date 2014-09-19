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

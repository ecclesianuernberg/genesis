from PIL import Image
from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField
import wtforms.validators as validators


def image_resize(in_filename, out_filename, size=800):
    img = Image.open(in_filename)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img.save(out_filename)


class EditGroupForm(Form):
    name = StringField(
        'Name',
        validators=[validators.DataRequired()])
    short_description = StringField(
        'Kurze Beschreibung',
        validators=[validators.DataRequired()])
    long_description = TextAreaField(
        'Lange Beschreibung',
        validators=[validators.DataRequired()])
    active = BooleanField('Active')

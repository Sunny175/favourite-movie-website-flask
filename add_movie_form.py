from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField


class AddMovie(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

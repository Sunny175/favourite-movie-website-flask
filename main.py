from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from rate_movie_form import RateMovieForm
from add_movie_form import AddMovie

import requests

MOVIE_DB_API_KEY = "5c58b3c1c5635422a58225182511ef64"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# Create the extension
database = SQLAlchemy()

app = Flask(__name__)

# Set the secret key for the flask wtf forms
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# Configure the SQLite database, related to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-project.db"

# Enabling the bootstrap support in the app
Bootstrap(app)

# Initialize the app with the extension
database.init_app(app)


class Movie(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String, unique=True, nullable=False)
    year = database.Column(database.Integer)
    description = database.Column(database.String)
    rating = database.Column(database.Float)
    ranking = database.Column(database.Integer)
    review = database.Column(database.String)
    img_url = database.Column(database.String)


with app.app_context():
    database.create_all()


@app.route("/")
def home():
    new_movie = database.session.execute(database.select(Movie).order_by(Movie.id)).scalars()
    movie_list = []
    for movie in new_movie:
        movie_list.append(movie)
    for i in range(len(movie_list)):
        movie_list[i].ranking = len(movie_list) - i
    return render_template("index.html", movies=movie_list)


@app.route("/add_movie", methods=["POST", "GET"])
def add_movie():
    movie_form = AddMovie()
    if movie_form.validate_on_submit():
        movie_title = movie_form.movie_title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        similar_movie_list = []
        for movie_title in response.json()['results']:
            similar_movie_list.append([movie_title["id"], movie_title['original_title'], movie_title['release_date']])
        return render_template("select.html", similar_movie_list=similar_movie_list)
    return render_template("add.html", form=movie_form)


@app.route('/find')
def find_movie():
    movie_api_id = request.args.get("id")
    form = RateMovieForm()
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        movie = Movie(
            title=data["title"],
            description=data["overview"],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            year=int(data['release_date'].split('-')[0])
        )
        try:
            database.session.add(movie)
            database.session.commit()
        except exc.IntegrityError:
            database.session.rollback()
        return redirect(url_for("rate_movie", id=movie.id, form=form))


@app.route('/edit', methods=["POST", "GET"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = database.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        movie.verified = True
        database.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie = database.get_or_404(Movie, movie_id)
    database.session.delete(movie)
    database.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

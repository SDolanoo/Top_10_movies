from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Float, Column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
HEADERS = {
    "accept": "application/json",
    "Authorization": os.environ["BEARER_TOKEN"]
}

# CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    rating = Column(Float, nullable=True)
    ranking = Column(Integer, nullable=True)
    review = Column(String, nullable=True)
    img_url = Column(String, nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField(label="Your movie rating", validators=[DataRequired()])
    review = StringField(label="Make a review", validators=[DataRequired()])
    submit = SubmitField("Submit")

class AddMovieForm(FlaskForm):
    name = StringField(label="Name of the movie", validators=[DataRequired()])
    submit = SubmitField("Add movie")

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    movies_data = result.scalars().all()

    for i in range(len(movies_data)):
        movies_data[i].ranking = len(movies_data) - i
    db.session.commit()

    return render_template("index.html", movies=movies_data)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/edit", methods=["GET", "POST"])
def edit_page():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/add", methods=["GET", "POST"])
def add_page():
    form = AddMovieForm()
    if form.validate_on_submit():
        url = f"https://api.themoviedb.org/3/search/movie?query={form.name.data}&include_adult=true&language=en-US&page=1"
        response = requests.get(url, headers=HEADERS)
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/selected", methods=["GET", "POST"])
def movie_selected():
    movie_title = request.args.get("title")
    movie_date = request.args.get("date")
    url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&include_adult=false&language=en-US&primary_release_year={movie_date}&page=1"
    response = requests.get(url, headers=HEADERS)
    data = response.json()["results"][0]
    new_movie = Movie(
        title=data["original_title"],
        year=data["release_date"],
        description=data["overview"],
        rating=0.0,
        ranking="none",
        review="none",
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    )
    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)

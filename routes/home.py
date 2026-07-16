from flask import Blueprint
from flask import render_template

home = Blueprint(
    "home",
    __name__
)


@home.route("/")
def index():

    return render_template(
        "guest/index.html"
    )


@home.route("/about")
def about():

    return render_template(
        "guest/about.html"
    )


@home.route("/upload")
def upload():

    return render_template(
        "guest/upload.html"
    )
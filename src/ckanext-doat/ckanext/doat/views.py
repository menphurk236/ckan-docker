from flask import Blueprint


doat = Blueprint(
    "doat", __name__)


def page():
    return "Hello, doat!"


doat.add_url_rule(
    "/doat/page", view_func=page)


def get_blueprints():
    return [doat]

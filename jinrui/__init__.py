# -*- coding: utf-8 -*-
from flask import Flask
from flask import Blueprint
from flask_cors import CORS

from .api.AHello import AHello
from .api.AOcr import AOcr
from .api.APpt import APpt
from .api.APaper import APaper
from .api.AAnswer import AAnswer

from .extensions.request_handler import error_handler, request_first_handler
from .config.secret import DefaltSettig
from .extensions.register_ext import register_ext
from jinrui.extensions.base_jsonencoder import JSONEncoder
from jinrui.extensions.base_request import Request


def register(app):
    jr = Blueprint(__name__, 'jr', url_prefix='/api')
    jr.add_url_rule('/hello/<string:hello>', view_func=AHello.as_view('hello'))
    jr.add_url_rule('/ocr/<string:ocr>', view_func=AOcr.as_view('ocr'))
    jr.add_url_rule('/ppt/<string:ppt>', view_func=APpt.as_view('ppt'))
    jr.add_url_rule('/paper/<string:paper>', view_func=APaper.as_view('paper'))
    jr.add_url_rule('/answer/<string:answer>', view_func=AAnswer.as_view('answer'))
    app.register_blueprint(jr)


def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return resp


def create_app():
    app = Flask(__name__)
    app.json_encoder = JSONEncoder
    app.request_class = Request
    app.config.from_object(DefaltSettig)
    app.after_request(after_request)
    register(app)
    CORS(app, supports_credentials=True)
    request_first_handler(app)
    register_ext(app)
    error_handler(app)
    return app

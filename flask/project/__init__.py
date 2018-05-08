import os

from flask import Flask, jsonify

from .utils.loading import load_blueprints

application = Flask(__name__)
application.config['DEUBG'] = bool(int(os.environ['DEBUG']))

load_blueprints(application, '.api.v1')

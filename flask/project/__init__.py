import os
from flasgger import Swagger
from flask import Flask, jsonify

from .utils.loading import load_blueprints

application = Flask(__name__)
swagger = Swagger(application)
application.config['DEBUG'] = bool(int(os.environ['DEBUG']))

load_blueprints(application, '.api.v1')

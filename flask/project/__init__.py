import os
from flasgger import Swagger
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .utils.loading import load_blueprints

application = Flask(__name__)
swagger = Swagger(application)
application.config['DEBUG'] = bool(int(os.environ['DEBUG']))

load_blueprints(application, '.api.v1')


@application.errorhandler(HTTPException)
def handle_http_exception(error):
    if hasattr(error, 'json'):
        return error.json()
    else:
        return error

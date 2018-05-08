from flask import Flask, jsonify

from .utils.loading import load_blueprints

application = Flask(__name__)

load_blueprints(application, '.api.v1')

@application.errorhandler(Exception)
def handle_http_status_code(error):
    if hasattr(error, 'http_status_code'):
        if callable(getattr(error, 'payload', None)):
            response = error.payload()
            response.status_code = error.http_status_code
            return response
    raise error

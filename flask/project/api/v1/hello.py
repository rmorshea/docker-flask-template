from flask import Blueprint

from .auth import authorization
from .msg import response

hello = Blueprint('hello', __name__)


@hello.route('/hello-world')
@authorization
def world():
    """
    a hello world message
    ---
    parameters:
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer YOUR-TOKEN
        required: true
        description: any access token
    """
    return response(200, message='hello world')


@hello.route('/hello-universe')
@authorization
def universe():
    """
    a hello universe message
    ---
    parameters:
      - name: authorization
        in: header
        schema:
          type: string
          example: Bearer YOUR-TOKEN
        required: true
        description: any access token
    """
    return response(200, message='hello universe')

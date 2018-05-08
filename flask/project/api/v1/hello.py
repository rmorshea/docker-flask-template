from flask import Blueprint

from .auth import authorization
from .msg import response

hello = Blueprint('hello', __name__)


@hello.route('/hello-world')
@authorization
def world():
    return response(200, message='hello world')


@hello.route('/hello-universe')
@authorization
def universe():
    return response(200, message='hello universe')

import os
from redis import Redis

db = Redis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']))

import os
import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDISTOGO_URL', 'redis://redistogo:5c71930714e02c197e8d320eaccf66fa@soapfish.redistogo.com:10606/')
conn = redis.from_url(redis_url)


def main():
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        print("Running worker")
        worker.work(burst=True)
        print("Worker done")

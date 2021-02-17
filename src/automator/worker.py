import os
import redis
import logging
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDISTOGO_URL', 'redis://redistogo:5c71930714e02c197e8d320eaccf66fa@soapfish.redistogo.com:10606/')
conn = redis.from_url(redis_url)

# Define logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s: %(message)s')

file_handler = logging.FileHandler('log/errors.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def main():
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        logger.info("Running worker")
        worker.work(burst=True)
        logger.info("Worker done")

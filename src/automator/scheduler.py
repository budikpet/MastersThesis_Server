from datetime import datetime
from rq import Queue
from .worker import conn
from scrapers.zoo_scraper import run_test_job
import logging

q = Queue(connection=conn)

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


def add_web_scraping_job(interval_time: int):
    logger.info(
        f'JOB EXECUTED: This job is run every {interval_time}. Current time is: {datetime.now()}')
    # TODO: If no internet connection then reschedule here or in zoo_scraper
    result = q.enqueue(run_test_job)


def main():
    """
    Starts the script which is primarily to be used by Heroku scheduler to
    """
    logging.info('Scheduler script started.')

    logger.info('Scheduler script ended.')

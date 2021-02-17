from datetime import datetime
from rq import Queue
from .worker import conn
from scrapers.zoo_scraper import run_test_job
import logging
import os
import traceback
from enum import IntEnum
from configparser import ConfigParser
from server_dataclasses.interfaces import DBHandlerInterface

q = Queue(connection=conn)

# Define logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s: %(message)s')


os.makedirs('log', exist_ok=True)
file_handler = logging.FileHandler('log/errors.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class SchedulerStates(IntEnum):
    # Before update date
    WAIT = 0
    # Update date achieved, schedule job in RQ and start worker dyno
    START_UPDATE = 1
    # Worker dyno still working
    UPDATING = 2
    # Worker dyno has no more work, stop it and schedule another job date
    STOP_WORKER = 3


def add_web_scraping_job(interval_time: int):
    logger.info(
        f'JOB EXECUTED: This job is run every {interval_time}. Current time is: {datetime.now()}')
    # TODO: If no internet connection then reschedule here or in zoo_scraper
    result = q.enqueue(run_test_job)


def main():
    """
    Starts the script which behaves like a Finite State Machine that takes care of running scheduled jobs. Primarily started by Heroku Scheduler.
    """
    logger.info('Scheduler script started.')

    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base'] | cfg._sections['scrapers']
    cfg_dict['collection_name'] = 'metadata'

    handler_class: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler_class is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    with handler_class(**cfg_dict) as handler:
        try:
            handler: DBHandlerInterface = handler
            metadata: dict = next(iter(handler.find({"_id": 0})), None)
            scheduler_state: SchedulerStates = SchedulerStates(metadata.get('scheduler_state'))
            if(scheduler_state is None):
                scheduler_state = SchedulerStates.WAIT
                handler.update_one({"_id": 0}, data={'$set': {'scheduler_state': scheduler_state}})

            if(scheduler_state == SchedulerStates.WAIT):
                logger.info('WAIT')
            elif(scheduler_state == SchedulerStates.START_UPDATE):
                logger.info('START_UPDATE')
            elif(scheduler_state == SchedulerStates.UPDATING):
                logger.info('UPDATING')
            elif(scheduler_state == SchedulerStates.STOP_WORKER):
                logger.info('STOP_WORKER')
            else:
                raise RuntimeError(f'Unknown scheduler state: {scheduler_state}')
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())

    logger.info('Scheduler script ended.')

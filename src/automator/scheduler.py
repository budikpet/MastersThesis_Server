from datetime import datetime
from rq import Queue
from .worker import conn
import scrapers.zoo_scraper as zoo_scraper
import scrapers.map_downloader as map_downloader
import logging
import os
import traceback
from configparser import ConfigParser
from server_dataclasses.interfaces import DBHandlerInterface
from server_dataclasses.models import SchedulerStates, DynoStates
from datetime import datetime
import heroku3
from heroku3.models.app import App
from croniter import croniter

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


def __change_worker_dyno_state__(state: DynoStates, heroku_api_key: str, **kwargs):
    heroku_conn = heroku3.from_key(heroku_api_key)
    app: App = heroku_conn.app('budikpet-zoo-prague')
    app.scale_formation_process('worker', state)

def __schedule_long_job__():
    q = Queue(connection=conn, default_timeout=18000)
    q.enqueue(map_downloader.main)
    q.enqueue(zoo_scraper.main)

def handle_update(handler: DBHandlerInterface, heroku_api_key: str, config: dict, **kwargs):
    """
    Basically the FSM that handles scripts that need Heroku worker dyno to run.

    Handles scheduling updates and switching the worker dyno on/off.

    Args:
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
        heroku_api_key (str): An API key for Heroku.
        config (dict): Data from the configuration file.

    Raises:
        RuntimeError: Raised if a scheduler_state received from DB is unknown.
    """
    metadata: dict = next(iter(handler.find({"_id": 0})), None)
    logger.info(f'Received metadata: {metadata}')
    
    next_update: datetime = metadata.get('next_update', datetime.now())
    scheduler_state: SchedulerStates = SchedulerStates(metadata.get('scheduler_state'))
    if(scheduler_state is None):
        scheduler_state = SchedulerStates.WAIT
        handler.update_one({"_id": 0}, data={'$set': {'scheduler_state': scheduler_state}})

    if(scheduler_state == SchedulerStates.WAIT):
        if(next_update <= datetime.now()):
            # It is time to update the database
            logger.info('WAIT -> UPDATING')
            __schedule_long_job__()
            # Start worker dyno and update scheduler_state in DB
            __change_worker_dyno_state__(DynoStates.UP, heroku_api_key)
            handler.update_one({"_id": 0}, {"$set": {"scheduler_state": SchedulerStates.UPDATING}})
        else:
            logger.info('WAIT')
        
    elif(scheduler_state == SchedulerStates.UPDATING):
        logger.info('UPDATING')
        diff = datetime.now() - metadata['last_update_start']
        if((diff.days * 24 + diff.seconds / 3600) > 8.0):
            # The script probably got stuck, reset needed
            logger.info('UPDATING -> WAIT')
            __change_worker_dyno_state__(DynoStates.DOWN, heroku_api_key)
            handler.update_one({"_id": 0}, {"$set": {"scheduler_state": SchedulerStates.WAIT}})

    elif(scheduler_state == SchedulerStates.WORK_DONE):
        # This state should be set only by zoo_scraper
        logger.info('WORK DONE -> WAIT')
        __change_worker_dyno_state__(DynoStates.DOWN, heroku_api_key)

        # Schedule next update
        crontab_schedule: str = os.getenv('CRONTAB_SCHEDULE', config['default_crontab_schedule'])
        crontab: croniter = croniter(crontab_schedule, datetime.now())
        handler.update_one({"_id": 0}, {"$set": {"next_update": crontab.get_next(datetime), "scheduler_state": SchedulerStates.WAIT}})
    else:
        raise RuntimeError(f'Unknown scheduler state: {scheduler_state}')

def main():
    """
    Starts the script which behaves like a Finite State Machine (FSM) that takes care of running scheduled jobs. Primarily started by Heroku Scheduler.
    """
    logger.info('Scheduler script started.')

    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base']
    cfg_dict['collection_name'] = 'metadata'

    handler_class: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler_class is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    heroku_api_key: str = os.getenv('HEROKU_API_KEY', False)
    if not heroku_api_key:
        raise Exception(f'Environmental variable HEROKU_API_KEY not specified.')

    with handler_class(**cfg_dict) as handler:
        try:
            handle_update(handler, config=cfg_dict, heroku_api_key=heroku_api_key)
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())

    logger.info('Scheduler script ended.')

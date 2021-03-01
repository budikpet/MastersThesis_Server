import feedparser
import logging
import traceback
import os
from configparser import ConfigParser
from server_dataclasses.interfaces import DBHandlerInterface

_URL: str = "https://www.zoopraha.cz/?format=feed&type=rss"                         # Novinky
_URL2: str = 'https://www.zoopraha.cz/rss-export/akce-v-zoo-praha'                  # Akce v Zoo Praha, pouze nadpisy
_URL3: str = 'https://www.zoopraha.cz/rss-export/akce-v-zoo-praha-fullarticle'      # Akce v Zoo Praha, plný text


# Define logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s: %(message)s')

os.makedirs('log', exist_ok=True)
file_handler = logging.FileHandler('log/errors.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

warning_handler = logging.FileHandler('log/warnings.log')
warning_handler.setLevel(logging.WARN)
warning_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(warning_handler)

def update_news(db_handler: DBHandlerInterface, **kwargs):
    """
    Downloads & parser Zoo Prague new RSS feed.

    Stores data in DB for later access.

    Args:
        db_handler (DBHandlerInterface): [description]
    """
    # TODO: Implement
    rss_data = feedparser.parse(_URL)

def main():
    """
    Run RSS Parser of Zoo Prague news.
    """

     # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base']
    cfg_dict['collection_name'] = 'news'

    handler: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    with handler(**cfg_dict) as handler_instance:
        try:
            update_news(handler_instance)
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())
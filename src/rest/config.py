from functools import lru_cache
from configparser import ConfigParser
import os
from server_dataclasses.interfaces import DBHandlerInterface
from types import SimpleNamespace

@lru_cache
def get_settings() -> dict:
    # Check S3 environment vars
    s3_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'AWS_STORAGE_BUCKET_NAME']
    s3_missing_vars = list(filter(lambda env_var: env_var not in os.environ, s3_env_vars))
    if(len(s3_missing_vars) != 0):
        raise RuntimeError(f'Environment variables "{s3_missing_vars}" not set.')

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base']
    cfg_dict['collection_name'] = 'zoo_data'

    if cfg_dict.get('used_db') is None:
        raise Exception(f'No DBHandler specified in config file.')

    # Get the required db_handler instance
    handler: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    res = {
        'aws_storage_bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
        'map_file_prefix': cfg['mbtiles_downloader']['output'],
        'handler_class': handler
    }
    
    return SimpleNamespace(**(res | cfg_dict))
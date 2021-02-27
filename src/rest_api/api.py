from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
from pathlib import Path
from configparser import ConfigParser
import logging
import traceback
from server_dataclasses.interfaces import DBHandlerInterface
import boto3
from botocore.exceptions import ClientError

#TODO Create app using a method which initializes configs

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

# Get data from the config file into a flat dictionary
cfg: ConfigParser = ConfigParser()
cfg.read('config/config.cfg')
cfg_dict: dict = cfg._sections['base']
# cfg_dict['collection_name'] = 'zoo_data'

if cfg_dict.get('used_db') is None:
    raise Exception(f'No DBHandler specified in config file.')

# Get the required db_handler instance
handler: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
if handler is None:
    raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

# Create app
app = FastAPI()

#######################################################################################
#################### Create API interface #############################################
#######################################################################################

@app.get('/')
async def index():
    return {'status': 'FastAPI application running.'}

@app.get('/animals')
async def animals(only_currently_available: bool = True):

    return None

@app.get('/mapdata')
async def map_data():
    file_prefix: str = cfg['mbtiles_downloader']['output']
    filename: str = f'{file_prefix}.mbtiles'
    mbtiles_path = Path(f'./tmp/{file_prefix}/{filename}')

    if(not mbtiles_path.is_file()):
        # Download & cache mbtiles file
        os.makedirs(mbtiles_path.parent, exist_ok=True)
        client = boto3.client('s3')
        client.download_file(os.getenv('AWS_STORAGE_BUCKET_NAME'), filename, mbtiles_path)

    logger.info(f'Returning file called "{filename}"')
    return FileResponse(mbtiles_path, media_type='application/octet-stream', filename=filename)
import traceback
import logging
import os
import tilepack.builder as tilepack
from glob import iglob
from configparser import ConfigParser
from pathlib import Path
import shutil
import zipfile
import json
from server_dataclasses.interfaces import DBHandlerInterface


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

def download_map_data(args: dict) -> Path:
    """
    Use tilepack tool to download MBTiles & GeoJSON.

    Data is downloaded and stored in files which are then moved under './tmp' directory.

    Args:
        args (dict): All arguments for tilepack tool.
    """
    try:
        tilepack.build_tile_packages(**args)
    except:
        logger.error('Error occured in tilepack tool when downloading MBTiles & GeoJSON')
        logger.error(traceback.format_exc())

    # Move created files into a folder
    file_prefix = args['output']
    folder_path = 'tmp' / Path(file_prefix)
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

    os.makedirs(folder_path)
    for file in iglob(f'{file_prefix}*.*'):
        shutil.move(file, folder_path)
        
    # Unzip GeoJSON files
    geojson_path = folder_path / 'geojsons'
    with zipfile.ZipFile(folder_path / f'{file_prefix}.zip', 'r') as zip_ref:
        zip_ref.extractall(geojson_path)

    return folder_path

def parse_data(folder_path: Path, db_handler: DBHandlerInterface):
    """
    Parses GeoJSON data for data that needs to be integrated with Zoo Prague data.

    Args:
        folder_path (Path): Path to a parent folder of map data files we downloaded.
        db_handler (DBHandlerInterface): [description]
    """
    res: dict = dict()
    for geojson in iglob(str(folder_path / 'geojsons' / 'all' / '**/*.json'), recursive=True):
        with open(geojson) as f:
            data = json.load(f)
            for poi in data['pois']['features']:
                poi = poi['properties']
                if(poi['kind'] == 'animal'):
                    res[poi['id']] = poi['name']

    res = [{"_id": k, "name": v} for k,v in res.items()]
    db_handler.drop_collection()
    db_handler.insert_many(res)

def main():
    """
    Run MBTiles & GeoJSON map data downloader/parser.
    """

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['mbtiles_downloader'] | cfg._sections['base'] | cfg._sections['scrapers']
    cfg_dict['collection_name'] = 'map_data'

    mapzen_url_prefix = os.getenv('MAPZEN_URL_PREFIX', 'https://tile.nextzen.org/tilezen')
    mapzen_api_key = os.getenv('MAPZEN_API_KEY', None)
    if(mapzen_api_key is None):
        raise RuntimeError('Environmental variable MAPZEN_API_KEY is not set.')

    handler: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    args = {
        'min_lon': float(cfg_dict['min_lon']),
        'min_lat': float(cfg_dict['min_lat']),
        'max_lon': float(cfg_dict['max_lon']),
        'max_lat': float(cfg_dict['max_lat']),
        'min_zoom': int(cfg_dict['min_zoom']),
        'max_zoom': int(cfg_dict['max_zoom']),
        'output': cfg_dict['output'],
        'tile_size': 512,
        'tile_format': 'json',
        'output_formats': ['mbtiles', 'zipfile'],
        'layer': 'all',
        'type': 'vector',
        'tile_compression': False,
        'concurrency': 1,
        'api_key': mapzen_api_key,
        'url_prefix': mapzen_url_prefix
    }

    with handler(**cfg_dict) as handler_instance:
        try:
            # TODO: Uncomment
            # folder_path: Path = download_map_data(args)
            folder_path: Path = Path(f'tmp/{args["output"]}')
            parse_data(folder_path, handler_instance)
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())

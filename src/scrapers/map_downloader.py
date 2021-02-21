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
from bs4 import BeautifulSoup, Tag
import requests
import csv
import itertools
import time
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

warning_handler = logging.FileHandler('log/warnings.log')
warning_handler.setLevel(logging.WARN)
warning_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(warning_handler)

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

def parse_data(folder_path: Path, db_handler: DBHandlerInterface) -> list[dict[int, str]]:
    """
    Parses GeoJSON data for data that needs to be integrated with Zoo Prague data.

    Args:
        folder_path (Path): Path to a parent folder of map data files we downloaded.
        db_handler (DBHandlerInterface): [description]

    Returns:
        list[dict[int, str]]: A list of animal pen data that was parsed from GeoJSONs.
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
    return res

def __get_csv_data__() -> list[dict[str, list]]:
    """
    Reads data from config/singular_plural.csv which holds initialization data for singular_plural collection.

    Returns:
        list[dict[str, list]]: Parsed data
    """
    p = 'config/singular_plural.csv'
    data: list = list()
    if(os.path.isfile(p)):
        with open(p) as f:
            csv_reader = csv.reader(f, delimiter=';')
            for plural, singulars in csv_reader:
                singulars = [singular.strip() for singular in singulars.split(',')]
                data.append({"_id": plural, "singulars": singulars})

    return data

def get_singular(plural: str, session: requests.Session, singular_plural_data: list, collection_name: str, min_delay: float) -> str:
    """
    Returns a singular for the given plural.

    Primarily returns from the singular_plural collection. If the value is not found then tries to find the value in an online dictionary.

    Args:
        plural (str): [description]
        session (requests.Session): [description]
        db_handler (DBHandlerInterface): [description]
        collection_name (str): Name of the collection where the values can be found.

    Returns:
        str: Singular value found either in a collection or using an online dictionary. Otherwise returns None.
    """
    if(singular_plural_data[plural] is not None):
        # Word found in the collection
        return singular_plural_data[plural]

    # Check the online dictionary
    time.sleep(min_delay)
    page = requests.get(f'https://prirucka.ujc.cas.cz/?slovo={plural}')
    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.find("table")

    if(table is None):
        logger.warn(f'No singulars found for a plural "{plural}".')
        return None

    if(table.a is not None):
        # Remove links which can appear in the table and which mess up the text
        table.a.decompose()

    rows = table.find_all('tr')
    if(len(rows) != 8):
        logger.warn(f'No singulars found for a plural "{plural}".')
        return None

    _, singular, found_plurals = rows[1].find_all('td')
    plurals = found_plurals.text.split(',')
    plurals = [v.strip() for v in plurals]

    if(plural in plurals):
        return [singular.text]

    logger.warn(f'No singulars found for a plural "{plural}".')
    return None

def update_singular_plural_table(session: requests.Session, db_handler: DBHandlerInterface, pens: list[dict[int, str]], min_delay: float):
    collection_name: str = 'singular_plural'
    if(not db_handler.collection_exists(collection_name=collection_name)):
        # Init singular_plural collection
        data = __get_csv_data__()
        db_handler.insert_many(data, collection_name=collection_name)

    singular_plural_data = db_handler.find({}, collection_name=collection_name)
    singular_plural_data = {d["_id"]:d["singulars"] for d in singular_plural_data}
    
    for pen in pens:
        # Some pens can have multiple animals
        res: list = list()
        names = pen['name'].strip().split(',')
        for name in names:
            # Some names can have noun and pronoun
            words = name.strip().split(' ')
            if(len(words) == 1):
                # Has only noun
                singulars = get_singular(words[0], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                if(singulars is not None):
                    db_handler.update_one({"_id": words[0]}, {"$set": {"singulars": singulars}}, upsert=True, collection_name=collection_name)
                    res.append(singulars[0])
            elif(len(words) == 2):
                # Has noun and pronoun
                singular_noun = get_singular(words[0], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                singular_pronouns = get_singular(words[1], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                if(singular_noun is not None and singular_pronouns is not None):
                    db_handler.update_one({"_id": words[0]}, {"$set": {"singulars": singular_noun}}, upsert=True, collection_name=collection_name)
                    db_handler.update_one({"_id": words[1]}, {"$set": {"singulars": singular_pronouns}}, upsert=True, collection_name=collection_name)
                    for pair in itertools.product(singular_noun, singular_pronouns):
                        res.append(' '.join(pair))

        res

def main():
    """
    Run MBTiles & GeoJSON map data downloader/parser.
    """

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['mbtiles_downloader'] | cfg._sections['base'] | cfg._sections['scrapers']
    cfg_dict["min_delay"] = float(os.getenv('MIN_SCRAPING_DELAY', cfg_dict["min_delay"]))
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

    with requests.Session() as session, handler(**cfg_dict) as handler_instance:
        try:
            # TODO: Uncomment
            # folder_path: Path = download_map_data(args)
            folder_path: Path = Path(f'tmp/{args["output"]}')
            pens = parse_data(folder_path, handler_instance)

            # Animal pens are plural, need singular versions for joining with Zoo Prague lexicon data.
            update_singular_plural_table(session, handler_instance, pens, cfg_dict["min_delay"])
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())

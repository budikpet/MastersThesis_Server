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
import boto3
from botocore.exceptions import ClientError
from server_dataclasses.interfaces import DBHandlerInterface

# Definitions
LineCoords = list[tuple[float, float]]
MultiCoords = list[LineCoords]

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

def download_map_data(args: dict, bucket_name: str) -> Path:
    """
    Use tilepack tool to download MBTiles & GeoJSON.

    Data is downloaded and stored in files which are then moved under './tmp' directory.

    Args:
        args (dict): All arguments for tilepack tool.

    Returns:
        Path: Path to the folder where downloaded map data was stored.
    """
    try:
        logger.info('Downloading map data.')
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

    # Upload MBTiles to AWS S3
    mbtiles_name: str = f'{file_prefix}.mbtiles'
    mbtiles_path: str = str(folder_path / mbtiles_name)
    client = boto3.client('s3')
    response = client.upload_file(mbtiles_path, bucket_name, mbtiles_name)

    return folder_path

def __create_map_location__(poi: dict, is_animal_pen: bool = False) -> dict:
    """
    Create a new animal_pens/zoo_parts document.

    Args:
        poi (dict): Currently picked point data.

    Returns:
        dict: Created map location data.
    """
    props = poi['properties']
    geom = poi['geometry']
    _type = geom['type']
    coords = geom['coordinates']

    if(_type == 'Point'):
        # Point has different structure of coordinates which needs to be normalized
        coords = [[[coords[0], coords[1]]]]

    res: dict = {
        'geometry': {
            '_type': _type,
            'coordinates': coords
        },
        'name': props['name'],
        'is_animal_pen': is_animal_pen,
        'is_building': (_type == 'Polygon'),
        '_id': props['id']
    }

    return res

def prepare_geometry(geometry: dict) -> dict:
    """
    Changes all geometries to MultiLineString type and each coordinate into a tuple.
    """
    coords = list()
    
    if(geometry['type'] == 'LineString'):
        coords = [[tuple(coord) for coord in geometry['coordinates']]]
    else:
        for line in geometry['coordinates']:
            coords.append([tuple(coord) for coord in line])
            
    return {
        'type': 'MultiLineString',
        'coordinates': coords
    }

def construct_one_line(starting_line: LineCoords, coords: MultiCoords):
    """
    Concatenate all line parts into one line.
    """
    while(len(coords) > 0):
        end_point = starting_line[-1]
        found_line = None
        for line in reversed(coords):
            if(end_point == line[0]):
                # Found a line that connects to the end of starting line
                found_line = line
                break
        
        if(found_line is None):
            return None
        else:
            coords.remove(found_line)
            starting_line.remove(end_point)
            starting_line.extend(found_line)
    
    return starting_line

def find_starting_line(line_parts: MultiCoords) -> LineCoords:
    """
    Finds a line whose starting coordinate is not at the end of any other line.
    """
    for starting_line in reversed(line_parts):
        found_starting_line = True
        start_coord = starting_line[0]
        for line in reversed(line_parts):
            if start_coord == line[-1]:
                found_starting_line = False
                break
        
        if(found_starting_line == True):
            break
            
    if(found_starting_line == False):
        # Starting line not found
        return None
    
    line_parts.remove(starting_line)
    
    return starting_line

def remove_duplicate_lines(line_parts: MultiCoords):
    duplicates = set()
    line_parts.reverse()
    
    for line in line_parts:
        cnt = 0
        sline = tuple(line)
        for other_line in line_parts:
            if(sline == tuple(other_line)):
                cnt += 1
        
        if(cnt > 1):
            duplicates.add((cnt - 1, sline))
    
    for (count, duplicate) in duplicates:
        for _ in range(count):
            line_parts.remove(list(duplicate))

    line_parts.reverse()

def update_road(road: dict, line_string: LineCoords):
    road['geometry'] = {
        'type': 'LineString',
        'coordinates': line_string
    }

def cleanup_roads(roads: dict[int: dict]):
    """
    Transforms geometries of all roads into a LineString by connecting all its parts into one line.

    Args:
        roads (dict[int): All roads parsed from GeoJSONS. Roads with the same ID had their coordinates merged already.
    """
    removed_roads = list()
    unconstructed_roads = list()
    for road in roads.values():
        _id: int = road['properties']['id']
        road['_id'] = _id
        coords = road['geometry']['coordinates']

        if(len(coords) == 1):
            # This line has only one part so it does not need to be connected
            update_road(road, coords[0])
            continue

        remove_duplicate_lines(coords)
        
        starting_line: LineCoords = find_starting_line(coords)
        
        if(starting_line is None):
            # These roads do not matter in Zoo Prague
            logger.error("Could not find starting line for {}".format(_id))
            removed_roads.append(_id)
            continue
        
        line_string: LineCoords = construct_one_line(starting_line, coords)
        
        if(line_string is None):
            coords.append(starting_line)
            unconstructed_roads.append(_id)
            continue
        
        update_road(road, line_string)
    
    for _id in removed_roads:
        roads.pop(_id, None)

    if((length := len(unconstructed_roads)) > 1):
        logger.error(f'Could not automatically process {length} roads with ids: {unconstructed_roads}.')

def zoo_parts_manual_update(zoo_parts: dict):
    """
    Updates zoo_parts data using a provided CSV file.

    Args:
        zoo_parts (dict): Parsed zoo parts and buildings.
    """

    # Update zoo_parts, mainly because some have slightly different names in Zoo data and map data
    p = 'config/manual_zoo_parts.csv'
    if(os.path.isfile(p)):
        with open(p) as f:
            next(f) # skip first line
            csv_reader = csv.reader(f, delimiter=';')
            for _id, name in csv_reader:
                _id = int(_id)
                if(_id in zoo_parts):
                    zoo_parts[_id]['name'] = name

def roads_manual_update(roads: dict):
    """
    Updates roads data using a provided JSON file.

    Args:
        roads (dict): [description]
    """
    p = 'config/manual_roads.json'
    if(os.path.isfile(p)):
        with open(p) as f:
            for road in json.load(f):
                _id = road['_id']
                if(_id in roads):
                    road['geometry']['coordinates'] = [tuple(coord) for coord in road['geometry']['coordinates']]
                    roads[_id]['geometry'] = road['geometry']

    # Remove roads that were not repaired
    roads_to_remove = [road['_id'] for road in roads.values() if road['geometry']['type'] != 'LineString']
    for road_id in roads_to_remove:
        roads.pop(road_id)

def prepare_road_nodes(roads: dict[int: dict]) -> dict[int: dict]:
    """
    Creates a list of road nodes where each knows to which road it belongs to.
    These nodes create roadmap graph of Zoo Prague.

    Returns:
        dict[int: dict]: Dictionary of road nodes.
    """

    road_nodes: dict[int: dict] = dict()
    for road in roads.values():
        for node in road['geometry']['coordinates']:
            _id = hash(node) % (10 ** 9)
            if(_id in road_nodes):
                # Node already exists, add road id
                road_nodes[_id]['road_ids'].add(road['_id'])
            else:
                # New node found
                road_nodes[_id] = {
                    '_id': _id,
                    'lon': node[0],
                    'lat': node[1],
                    'road_ids': {road['_id']}
                }

    # road_nodes = {k:v for k,v in road_nodes.items() if len(v['road_ids']) > 1}

    for node in road_nodes.values():
        road_ids = node['road_ids']
        node['road_ids'] = list(road_ids)
        node['is_connector'] = len(road_ids) > 1

    return road_nodes

def update_roads_with_nodes(roads: dict[int: dict], road_nodes: dict[int:dict]):
    """
    Transforms coordinates in roads from basic coordinates into full nodes.

    Args:
        roads (dict[int: dict]): All roads.
        road_nodes (dict[int: dict]): All nodes.
    """
    node_values = list(road_nodes.values())
    for road in roads.values():
        geometry = road['geometry']
        nodes: list[dict] = list()
        for coord in geometry['coordinates']:
            lon, lat = coord[0], coord[1]
            for node_value in node_values:
                if(node_value['lon'] == lon and node_value['lat'] == lat):
                    # Node found
                    nodes.append(node_value)
                    break
            
        road['geometry']['coordinates'] = nodes

def parse_map_data(folder_path: Path, db_handler: DBHandlerInterface) -> list[dict[int, str]]:
    """
    Parses GeoJSON data for data that needs to be integrated with Zoo Prague data.

    Most data is stored to MongoDB immediately, animal pens data is returned for further refinement.

    Args:
        folder_path (Path): Path to a parent folder of map data files we downloaded.
        db_handler (DBHandlerInterface): [description]

    Returns:
        list[dict[int, str]]: A list of animal pen data that was parsed from GeoJSONs.
    """
    animal_pens: dict = dict()
    zoo_parts: dict = dict()
    roads: dict[int: dict] = dict()
    for geojson in iglob(str(folder_path / 'geojsons' / 'all' / '**/*.json'), recursive=True):
        with open(geojson) as f:
            data = json.load(f)

            # Animal pens and some zoo buildings and parts
            for poi in data['pois']['features']:
                props = poi['properties']
                if(not props.get('id')):
                    continue

                id_: int = props['id']
                if(props['kind'] == 'animal'):
                    animal_pens[id_] = __create_map_location__(poi, is_animal_pen=True)
                elif(props['kind'] == 'zoo_part'):
                    if(props.get('label_placement') is None):
                        zoo_parts[id_] = __create_map_location__(poi)
            
            # Buildings
            for poi in data['buildings']['features']:
                props = poi['properties']
                if(props['kind'] == 'building' and props.get("id") is not None and props.get("name") is not None and props.get('label_placement') is None):
                    id_: int = props['id']
                    zoo_parts[id_] = __create_map_location__(poi)

            # Roads
            for road in data['roads']['features']:
                if((access := road['properties'].get('access')) is not None):
                    if(access == 'private'):
                        # Do not use private roads
                        continue
                
                _id = road['properties']['id']
                road['geometry'] = prepare_geometry(road['geometry'])
                
                if(_id in roads):
                    # A road with the same id already found, add its coordinates to the already stored road
                    roads[_id]['geometry']['coordinates'].extend(road['geometry']['coordinates'])
                else:
                    roads[_id] = road

    cleanup_roads(roads)

    # Do manual updates
    zoo_parts_manual_update(zoo_parts)
    roads_manual_update(roads)

    # Final refinement of road nodes and roads
    road_nodes = prepare_road_nodes(roads)
    update_roads_with_nodes(roads, road_nodes)

    # Add collections to DB
    db_handler.drop_collection(collection_name='zoo_parts')
    db_handler.insert_many(data=zoo_parts.values(), collection_name='zoo_parts')

    db_handler.drop_collection(collection_name='roads')
    db_handler.insert_many(data=roads.values(), collection_name='roads')

    db_handler.drop_collection(collection_name='road_nodes')
    db_handler.insert_many(data=road_nodes.values(), collection_name='road_nodes')

    # Return animal_pens collection since it needs to be processed further
    return animal_pens.values()

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
    Returns a singular forms for the given plural form.

    The algorithm:
    - primarily returns data from the singular_plural DB table. 
    - if the value is not found then tries to find the value in an online dictionary
    - otherwise the value is passed to administrator as a warning

    Args:
        plural (str): Input plural form.
        session (requests.Session): HTTP session for online dictionary.
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
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

def update_animal_tables(session: requests.Session, db_handler: DBHandlerInterface, pens: list[dict[int, str]], min_delay: float):
    """
    Use new map data to update the DB tables that:
    
    - holds transformations between singular and plural forms of animal names. It is used to connect data from Zoo Prague lexicon and map data.
    - holds data about animal pens. Also connects these animal pens and Zoo Prague lexicon data using singular forms if possible.

    Args:
        session (requests.Session): HTTP session
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
        pens (list[dict[int, str]]): Map data of located animal pens in Zoo Prague.
        min_delay (float): Delay between HTTP requests.
    """
    collection_name: str = 'singular_plural'
    if(not db_handler.collection_exists(collection_name=collection_name)):
        # Init singular_plural collection
        data = __get_csv_data__()
        db_handler.insert_many(data, collection_name=collection_name)

    singular_plural_data = db_handler.find({}, collection_name=collection_name)
    singular_plural_data = {d["_id"]:d["singulars"] for d in singular_plural_data}
    
    for pen in pens:
        # Some pens can have multiple animals
        pen_animal_names: list = list()
        names = pen['name'].strip().split(',')
        for name in names:
            # Some names can have noun and pronoun
            words = name.strip().split(' ')
            if(len(words) == 1):
                # Has only noun
                singulars = get_singular(words[0], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                if(singulars is not None):
                    db_handler.update_one({"_id": words[0]}, {"$set": {"singulars": singulars}}, upsert=True, collection_name=collection_name)
                    pen_animal_names.append(singulars[0])
            elif(len(words) == 2):
                # Has noun and pronoun
                singular_noun = get_singular(words[0], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                singular_pronouns = get_singular(words[1], session, singular_plural_data, collection_name=collection_name, min_delay=min_delay)
                if(singular_noun is not None and singular_pronouns is not None):
                    db_handler.update_one({"_id": words[0]}, {"$set": {"singulars": singular_noun}}, upsert=True, collection_name=collection_name)
                    db_handler.update_one({"_id": words[1]}, {"$set": {"singulars": singular_pronouns}}, upsert=True, collection_name=collection_name)
                    for pair in itertools.product(singular_noun, singular_pronouns):
                        pen_animal_names.append(' '.join(pair))

        pen["singular_names"] = pen_animal_names
    
    db_handler.drop_collection()
    db_handler.insert_many(pens)

def main():
    """
    Run MBTiles & GeoJSON map data downloader/parser.

    Downloads vector map data in MBTiles file and GeoJSON files. Stores the MBTiles file in AWS S3 DB and other data in the main DB.
    """

    # Check S3 environment vars
    s3_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'AWS_STORAGE_BUCKET_NAME']
    s3_missing_vars = list(filter(lambda env_var: env_var not in os.environ, s3_env_vars))
    if(len(s3_missing_vars) != 0):
        raise RuntimeError(f'Environment variables "{s3_missing_vars}" not set.')

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['mbtiles_downloader'] | cfg._sections['base']
    cfg_dict["min_delay"] = float(os.getenv('MIN_SCRAPING_DELAY', cfg_dict["min_delay"]))
    cfg_dict['collection_name'] = 'animal_pens'

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
            folder_path: Path = download_map_data(args, os.getenv('AWS_STORAGE_BUCKET_NAME'))
            pens = parse_map_data(folder_path, handler_instance)

            update_animal_tables(session, handler_instance, pens, cfg_dict["min_delay"])
        except ClientError as ex:
            logger.error('Error occured when uploading files to AWS S3.')
            logger.error(traceback.format_exc())
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())

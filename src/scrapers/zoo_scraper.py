from server_dataclasses.interfaces import DBHandlerInterface
from server_dataclasses.models import AnimalData, SchedulerStates
import requests
import time
import re
import os
from configparser import ConfigParser
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urljoin, ParseResult
import traceback
import logging
from datetime import datetime

# Define global vars
_URL: ParseResult = urlparse(
    "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat")
_MULTI_WHITESPACE = re.compile(r"\s+")

# Used for splitting strings such as 'group 1 str (group 2 str)' into two substrings
# Group 1 matches everything before the first '(', group 2 matches everything inside outermost '()'
_OUTSIDE_INSIDE_PARANTHESIS = re.compile(r'([^\(]*)\((.*)\)$')

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


def get_animal_urls(session: requests.Session) -> list[ParseResult]:
    """
    Parses

    Args:
        session (requests.Session): The used HTTP session.

    Returns:
        list[ParseResult]: [description]

    Yields:
        Iterator[list[ParseResult]]: [description]
    """
    page = session.get(_URL.geturl())
    soup = BeautifulSoup(page.content, 'html.parser')

    alphabetical_groups = soup.find(id="accordionAbeceda")\
        .find_all("div", class_="para")

    for alphabetical_group in alphabetical_groups:
        links = alphabetical_group.find_all('a')
        for link in links:
            if link is not None:
                yield urlparse(link["href"])


def get_animal_id(query_param: str) -> int:
    """
    Parses ID of an animal into

    Args:
        query_param (str): [description]

    Returns:
        int: [description]
    """
    g = (tuple(d.split('=')) for d in query_param.split('&'))
    query_dict: dict = {v[0]: v[1] for v in g}
    _id = query_dict.get("start", None)
    if _id is None:
        raise RuntimeError(f'Value of _id not found in query params: [{query_param}]')
    return int(_id)


def parse_unlinked_paragraphs(data: Tag) -> dict[str, str]:
    """
    Parse interesting_data and about_placement_in_zoo_prague Animal data.
    This data consists of <h3> tags and multiple <p> tags which. 
    It also might not always be flat hierarchy which makes it difficult to parse.

    Args:
        data (Tag): Part of parsed input data where the Animal data we are looking for is located.

    Returns:
        dict[str, str]: Key is the paragraph title (<h3> tag), value is the whole paragraph (joined <p> tags).
    """
    # TODO: Need to make proper test for this one since it probably doesn't work properly all the time. Need to test all combinations of non-flat hierarchies.
    res: dict[str, list[str]] = dict()
    last_h3_text: str = ''
    tags_to_check: set[str] = {'h3', 'p'}
    for tag in data.find_all(tags_to_check):
        if(tag.name == 'h3'):
            # Following <p> tags now belong to this <h3> tag
            last_h3_text = tag.text
            res[last_h3_text] = set()
            continue

        if(len(tag.contents) == 1):
            # Tag is flat, add it to the data
            res[last_h3_text].add(tag.text.strip())
        else:
            # Tag has children.
            children_names = [t.name for t in tag.children]
            if(tags_to_check.isdisjoint(children_names)):
                # Tag has children but these children aren't <h3> or <p> tags
                # If it had either <h3> or <p> tag it would cause duplicates
                res[last_h3_text].add(tag.text.strip())

    return {key: '\n'.join(value).strip() for key, value in res.items()}


def parse_table_data(table: Tag) -> dict[str, str]:
    """
    Parses data from <table> tag found at Zoo Prague lexicon site.

    Args:
        table (Tag): The <table> tag.

    Returns:
        dict[str, str]: Key is the title of the row.
    """
    res: dict[str, str] = dict()
    for row in table.find_all('tr'):
        data = row.find_all(['th', 'td'])
        res[data[0].text.strip()] = data[1].text.strip() if len(
            data) == 2 else None

    return res


def __add_parsed_table_data__(res: AnimalData, attrs: list[str], parsed_value: str):
    """
    Simplification function.

    There are attributes in AnimalData such as :py:attr:`AnimalData.food` and :py:attr:`AnimalData.food_detail` that are found in a table row in the HTML page.
    This function finds them and properly populates them in AnimalData object.

    Args:
        res (AnimalData): Animal data object of the currently parsed HTML page.
        attrs (list[str]): Attributes to set in the AnimalData object.
        parsed_value (str): The value where unparsed values are.
    """
    if parsed_value is None:
        return

    tmp = _OUTSIDE_INSIDE_PARANTHESIS.search(parsed_value)
    if (tmp is not None):
        setattr(res, attrs[0], tmp.group(1).strip())
        setattr(res, attrs[1], tmp.group(2).strip())
    else:
        setattr(res, attrs[0], parsed_value.strip())

def __add_map_locations__(animalData: AnimalData, animal_pens: list[dict], buildings: list[dict]):
    """
    Populates :py:attr:`AnimalData.map_locations` attribute.

    Finding locations:

    - firstly tries to find animals in animal pens found using map data
    - then tries to find animals in zoo houses using the official data from Zoo Prague.

    Args:
        res (AnimalData): Animal data object of the currently parsed HTML page.
        animal_pens (list[dict]): List of animal pens found in map data.
        buildings (list[dict]): List of buildings and zoo parts found in official data and map data.
    """
    # Add map locations for animals located in pens
    animalData.map_locations = [pen for pen in animal_pens if animalData.name.lower() in pen['singular_names']]
    if(len(animalData.map_locations) == 0):
        # Pen for full name not found. There may be an animal pen only for the first name
        first_name: str = animalData.name.lower().split(' ')[0].strip()
        animalData.map_locations = [pen for pen in animal_pens if first_name in pen['singular_names']]

    # Add map locations for animals located in zoo houses
    if(animalData.location_in_zoo is not None):
        zoo_houses = [building for building in buildings if building['name'].lower() == animalData.location_in_zoo.lower()]
        if(len(zoo_houses) == 1):
            # This animal is in a zoo house / zoo part
            zoo_house = zoo_houses[0]
            if(zoo_house['is_building'] == True):
                # This animal is in a zoo house
                animalData.map_locations.append(zoo_house)


def parse_animal_data(soup: BeautifulSoup, url: ParseResult, animal_pens: list[dict], buildings: list[dict]) -> AnimalData:
    """
    Parses all data from the given page into the AnimalData object.

    Args:
        soup (BeautifulSoup): Page to parse.
        url (ParseResult): URL of the page to parse.
        animal_pens (list[dict]): List of animal pens available in Zoo Prague map data directly from DB.
        buildings (list[dict]): List of buildings in Zoo Prague map data directly from DB. Contains zoo houses and other parts where animals could reside.

    Returns:
        AnimalData: Object with data that was parsed from the page.
    """
    res: AnimalData = AnimalData()

    data = soup.find("div", class_='mainboxcontent largebox')
    mainboxtitle = data.find(class_='mainboxtitle')
    para1, para2 = data.find_all('div', class_='para')

    # Parse id
    res._id = get_animal_id(url.query)

    # Parse czech & latin name
    names: str = mainboxtitle.find("h2").text
    __add_parsed_table_data__(res, ['name', 'latin_name'], names)

    # Parse short summary & image URL
    res.base_summary = para1.find('strong').text.strip()
    tmp = para1.find('a', class_='thumbnail')
    if(tmp is not None):
        res.image = _URL.hostname + tmp["href"]

    # Parse interesting_data and about_placement_in_zoo_prague data
    unlinked_data_dict: dict[str, str] = parse_unlinked_paragraphs(para2)
    res.interesting_data = unlinked_data_dict.get('Zajímavosti')
    res.about_placement_in_zoo_prague = unlinked_data_dict.get(
        'Chov v Zoo Praha')

    # Parse table data
    table_data: dict[str, str] = dict()
    for table in para2.find_all('table'):
        table_data |= parse_table_data(table)

    # Add parsed table_data into res
    __add_parsed_table_data__(
        res, ['class_', 'class_latin'], table_data.get('Třída'))
    __add_parsed_table_data__(
        res, ['order', 'order_latin'], table_data.get('Řád'))
    __add_parsed_table_data__(
        res, ['continent', 'continent_detail'], table_data.get('Rozšíření'))
    __add_parsed_table_data__(
        res, ['biotop', 'biotop_detail'], table_data.get('Biotop'))
    __add_parsed_table_data__(
        res, ['food', 'food_detail'], table_data.get('Potrava'))
    res.sizes = table_data.get('Rozměry')
    res.reproduction = table_data.get('Rozmnožování')
    res.location_in_zoo = table_data.get('Umístění v Zoo Praha')

    # Check is_currently_available
    if(res.about_placement_in_zoo_prague is not None and 'nechováme' in res.about_placement_in_zoo_prague.lower()):
        # Some animals have indication that they aren't located in Zoo Prague
        res.is_currently_available = False

    # Add map locations
    __add_map_locations__(res, animal_pens, buildings)

    return res


def run_web_scraper(session: requests.Session, db_handler: DBHandlerInterface, collection_name: str, min_delay: float = 10, **kwargs):
    """
    Run a Zoo Prague lexicon web scraper to fill the provided DB with data about animals.

    Args:
        session (requests.Session): HTTP session for running requests.
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
        min_delay (float): Minimum time in seconds to wait between downloads of pages to scrape.
    """
    animal_pens: list[dict] = db_handler.find(filter_={}, collection_name='animal_pens')
    buildings: list[dict] = db_handler.find(filter_={}, collection_name='zoo_parts')
    tmp_coll_name: str = f'tmp_{collection_name}'
    db_handler.update_one({'_id': 0}, {'$set': {'last_update_start': datetime.now()}}, upsert=True, collection_name='metadata')
    db_handler.drop_collection(collection_name=tmp_coll_name)

    for i, url in enumerate(get_animal_urls(session)):
        page = session.get(url.geturl())
        start_time: float = time.time()
        soup: BeautifulSoup = BeautifulSoup(page.content, 'html.parser')

        logger.info(f'{i}. {url.geturl()}')
        try:
            animal_data = parse_animal_data(soup, url, animal_pens, buildings)
            db_handler.insert_one(animal_data.__dict__, collection_name=tmp_coll_name)
        except:
            logger.error(f'Error occured when parsing: {url.geturl()}')
            logger.error(traceback.format_exc())
            continue

        elapsed_time: float = time.time() - start_time
        time_to_sleep: float = min_delay - elapsed_time
        logger.info(f'\t\tElapsed time: {elapsed_time} s')
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
    
    db_handler.drop_collection(collection_name=collection_name)
    db_handler.rename_collection(collection_new_name=collection_name, collection_name=tmp_coll_name)
    db_handler.update_one({'_id': 0}, {'$set': {'last_update_end': datetime.now()}}, upsert=True, collection_name='metadata')


def main():
    """
    Run Zoo Prague lexicon web scraper.

        Checks a `config.cfg` config file and runs the desired Zoo Prague lexicon scraper.
    """

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base']
    cfg_dict["min_delay"] = float(os.getenv('MIN_SCRAPING_DELAY', cfg_dict["min_delay"]))
    cfg_dict['collection_name'] = 'animals_data'

    if cfg_dict.get('used_db') is None:
        raise Exception(f'No DBHandler specified in config file.')

    # Get the required db_handler instance
    handler: DBHandlerInterface = next((handler for handler in DBHandlerInterface.__subclasses__() if handler.name == cfg_dict['used_db']), None)
    if handler is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    with requests.Session() as session, handler(**cfg_dict) as handler_instance:
        try:
            run_web_scraper(session, db_handler=handler_instance, **cfg_dict)
        except Exception as ex:
            logger.error('Unknown error occured')
            logger.error(traceback.format_exc())
        finally:
            # Work is done either successfully or unsuccessfully. Update scheduler_state
            logger.info('Setting scheduler_state to WORK_DONE.')
            handler_instance.update_one({"_id": 0}, {"$set": {"scheduler_state": SchedulerStates.WORK_DONE}}, collection_name='metadata')


def run_test_job():
    # main()
    with requests.Session() as s:
        res = [u for u in get_animal_urls(s)]
    logger.info(f'JOB DONE: Found {len(res)}')
    return "run_test_job return"

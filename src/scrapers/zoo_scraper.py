from server_dataclasses.interfaces import DBHandlerInterface
from server_dataclasses.models import AnimalData
import requests
import time
import re
from configparser import ConfigParser
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urljoin, ParseResult

_URL: ParseResult = urlparse("https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat")
_MULTI_WHITESPACE = re.compile(r"\s+")
_OUTSIDE_INSIDE_PARANTHESIS = re.compile(r'(.*)\((.*)\)')


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
    print("gen_animal_urls")
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
    # TODO: If ID is missing then write to a log
    g = (tuple(d.split('=')) for d in query_param.split('&'))
    query_dict: dict = {v[0]: v[1] for v in g}
    return int(query_dict["start"])

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
        res[data[0].text.strip()] = data[1].text.strip() if len(data) == 2 else None

    return res

def __add_parsed_table_data__(res: AnimalData, attrs: list[str], parsed_value: str):
    if parsed_value is None:
        return

    tmp = _OUTSIDE_INSIDE_PARANTHESIS.search(parsed_value)
    if (tmp is not None):
        setattr(res, attrs[0], tmp.group(1).strip())
        setattr(res, attrs[1], tmp.group(2).strip())
    else:
        setattr(res, attrs[0], parsed_value.strip())

def parse_animal_data(soup: BeautifulSoup, url: ParseResult) -> AnimalData:
    res: AnimalData = AnimalData()

    data = soup.find("div", class_='mainboxcontent largebox')
    mainboxtitle = data.find(class_='mainboxtitle')
    para1, para2 = data.find_all('div', class_='para')

    # Parse id
    res.id = get_animal_id(url.query)

    # Parse czech & latin name
    names: str = mainboxtitle.find("h2").text
    tmp = _OUTSIDE_INSIDE_PARANTHESIS.search(names)
    res.name = tmp.group(1).strip()
    res.latin_name = tmp.group(2).strip()

    # Parse short summary & image URL
    res.base_summary = para1.find('strong').text.strip()
    res.image = _URL.hostname + para1.find('a', class_ = 'thumbnail')["href"]

    # Parse interesting_data and about_placement_in_zoo_prague data
    unlinked_data_dict: dict[str, str] = parse_unlinked_paragraphs(para2)
    res.interesting_data = unlinked_data_dict.get('Zajímavosti')
    res.about_placement_in_zoo_prague = unlinked_data_dict.get('Chov v Zoo Praha')

    # Parse table data
    table_data: dict[str, str] = dict()
    for table in para2.find_all('table'):
        table_data |= parse_table_data(table)

    # Add parsed table_data into res
    __add_parsed_table_data__(res, ['class_', 'class_latin'], table_data.get('Třída'))
    __add_parsed_table_data__(res, ['order', 'order_latin'], table_data.get('Řád'))
    __add_parsed_table_data__(res, ['continent', 'continent_detail'], table_data.get('Rozšíření'))
    __add_parsed_table_data__(res, ['biotop', 'biotop_detail'], table_data.get('Biotop'))
    __add_parsed_table_data__(res, ['food', 'food_detail'], table_data.get('Potrava'))
    res.sizes = table_data.get('Rozměry')
    res.reproduction = table_data.get('Rozmnožování')
    res.location_in_zoo = table_data.get('Umístění v Zoo Praha')

    return res

def run_web_scraper(session: requests.Session, db_handler: DBHandlerInterface, min_delay: float = 10, **kwargs):
    """
    Run a Zoo Prague lexicon web scraper to fill the provided DB with data about animals.

    Args:
        session (requests.Session): HTTP session for running requests.
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
        min_delay (float): Minimum time in seconds to wait between downloads of pages to scrape.
    """
    animals_data: list[AnimalData] = list()
    for url in get_animal_urls(session):
        start_time: float = time.time()
        page = session.get(url.geturl())
        soup: BeautifulSoup = BeautifulSoup(page.content, 'html.parser')

        animal_data = parse_animal_data(soup, url)
        animals_data.append(animal_data)

        time_elapsed: float = time.time() - start_time
        time.sleep(min_delay - time_elapsed)
    
    db_handler.insert_many(animals_data)


def main():
    """
    Run Zoo Prague lexicon web scraper.

        Checks a `config.cfg` config file and runs the desired Zoo Prague lexicon scraper.
    """
    print("Running Zoo scraper.")

    # Get data from the config file into a flat dictionary
    cfg: ConfigParser = ConfigParser()
    cfg.read('config/config.cfg')
    cfg_dict: dict = cfg._sections['base'] | cfg._sections['scrapers']
    cfg_dict["min_delay"] = float(cfg_dict["min_delay"])

    if cfg_dict['used_db'] is None:
        raise Exception(f'No DBHandler specified in config file.')

    # Get the required db_handler instance
    cfg_dict['db_handler'] = next((x() for x in DBHandlerInterface.__subclasses__() if x.name == cfg_dict['used_db']), None)
    if cfg_dict['db_handler'] is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    with requests.Session() as session:
        run_web_scraper(session, **cfg_dict)


def run_test_job():
    urls = get_animal_urls()
    print(f'JOB DONE: Num of animals currently listed: {len(urls)}')
    return "run_test_job return"
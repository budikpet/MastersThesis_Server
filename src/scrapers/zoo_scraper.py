from server_dataclasses.interfaces import DBHandlerInterface
from server_dataclasses.models import AnimalData
import requests
import time
import re
from configparser import ConfigParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, ParseResult

_URL: str = "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat"
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
    page = session.get(_URL)
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

def parse_animal_data(soup: BeautifulSoup, url: ParseResult) -> AnimalData:
    res: AnimalData = AnimalData()
    data = soup.find("div", class_='mainboxcontent largebox')

    # Parse id
    res.id = get_animal_id(url.query)

    # Get czech & latin name
    names: str = data.find(class_='mainboxtitle').find("h2").text
    tmp = _OUTSIDE_INSIDE_PARANTHESIS.search(names)
    res.name = tmp.group(1).strip()
    res.latin_name = tmp.group(2).strip()

    pass

def run_web_scraper(session: requests.Session, db_handler: DBHandlerInterface, min_delay: float = 10, **kwargs):
    """
    Run a Zoo Prague lexicon web scraper to fill the provided DB with data about animals.

    Args:
        session (requests.Session): HTTP session for running requests.
        db_handler (DBHandlerInterface): A DBHandlerInterface instance of chosen database used to store data from Zoo Prague lexicon.
        min_delay (float): Minimum time in seconds to wait between downloads of pages to scrape.
    """
    print("run_web_scraper")
    for url in get_animal_urls(session):
        start_time: float = time.time()
        page = session.get(url.geturl())
        soup: BeautifulSoup = BeautifulSoup(page.content, 'html.parser')

        animal_data = parse_animal_data(soup, url)
        
        print(f'{id}: {url.geturl()}')

        time_elapsed: float = time.time() - start_time
        time.sleep(min_delay - time_elapsed)


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
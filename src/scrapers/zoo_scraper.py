from server_dataclasses.interfaces import DBHandlerInterface
import requests
import time
from configparser import ConfigParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, ParseResult

url: str = "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat"


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
    page = session.get(url)
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


def run_test_job():
    urls = get_animal_urls()
    print(f'JOB DONE: Num of animals currently listed: {len(urls)}')
    return "run_test_job return"


def run_web_scraper(session: requests.Session, db_handler: DBHandlerInterface, min_delay: float, **kwargs):
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
        id: int = get_animal_id(url.query)
        print(f'{id}: {url.geturl()}')


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

    if cfg_dict['used_db'] is None:
        raise Exception(f'No DBHandler specified in config file.')

    # Get the required db_handler instance
    cfg_dict['db_handler'] = next((x() for x in DBHandlerInterface.__subclasses__() if x.name == cfg_dict['used_db']), None)
    if cfg_dict['db_handler'] is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    with requests.Session() as session:
        run_web_scraper(session, **cfg_dict)

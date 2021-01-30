from server_dataclasses.interfaces import DataCollectorInterface, DBHandlerInterface
import requests
from configparser import ConfigParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def get_animal_urls():
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    animals_raw = soup.find(id="accordionAbeceda")\
        .find_all("div", class_="para")
    animals_url = list()

    for animal in animals_raw:
        links = animal.find_all('a')

        animals_url.extend([urlparse(link["href"]).geturl()
                            for link in links if link is not None])

    return animals_url


def run_test_job():
    urls = get_animal_urls()
    print(f'JOB DONE: Num of animals currently listed: {len(urls)}')
    return "run_test_job return"


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
    elif cfg_dict['lexicon_data_collector'] is None:
        raise Exception(
            f'No DataCollector for Prague Zoo lexicon specified in config file.')

    # Get the required db_handler instance
    cfg_dict['db_handler'] = next((x() for x in DBHandlerInterface.__subclasses__() if x.name == cfg_dict['used_db']), None)
    if cfg_dict['db_handler'] is None:
        raise Exception(f'DBHandler called "{cfg_dict["used_db"]}" not found.')

    # Get the required data collector instatance and start it
    data_collector: DataCollectorInterface = next((x() for x in DataCollectorInterface.__subclasses__() if x.name == cfg_dict['lexicon_data_collector']), None)
    if data_collector is None:
        raise Exception(
            f'DataCollector called "{cfg_dict["lexicon_data_collector"]}" not found.')

    data_collector.collect_data(**cfg_dict)

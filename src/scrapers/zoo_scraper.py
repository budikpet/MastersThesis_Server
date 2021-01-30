import requests
from configparser import ConfigParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

url = "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat"


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

	# Get data from the config file
	with open('config.cfg') as f:
		config_parser: ConfigParser = ConfigParser()
		config_parser.read_file(f)
from betamax_serializers.pretty_json import PrettyJSONSerializer
import betamax
import requests
import pytest
import time
from pytest_mock.plugin import MockerFixture
import os
from urllib.parse import urlparse, ParseResult
import scrapers.zoo_scraper as zoo_scraper
from fixtures import TestHandler
from server_dataclasses.models import AnimalData
from pathlib import Path

fixtures_path = f"{os.path.dirname(os.path.abspath(__file__))}/fixtures"

# def zoo_response_filter(interaction, cassette):
# 	print("Response filter")

# Configure betamax
betamax.Betamax.register_serializer(PrettyJSONSerializer)

with betamax.Betamax.configure() as config:
    cassettes_lib = f'{fixtures_path}/cassettes'

    if(not os.path.isdir(cassettes_lib)):
        os.makedirs(cassettes_lib)

    # tell Betamax where to find the cassettes
    config.cassette_library_dir = cassettes_lib
    config.default_cassette_options['record_mode'] = 'once'
    config.default_cassette_options['serialize_with'] = 'prettyjson'

    # Do changes before recording a cassette
    # config.before_record(callback=zoo_response_filter)


def test_get_animal_urls(betamax_session: requests.Session):
    """
    Test getting URLs of animals and what they look like.

    Args:
        betamax_session (requests.Session): [description]
    """
    urls: list[ParseResult] = [
        url for url in zoo_scraper.get_animal_urls(betamax_session)]

    assert len(urls) == 800
    assert None not in urls
    assert all([url.query != '' for url in urls])

    # Check if IDs of animals contain duplicates
    ids_set: set[int] = {zoo_scraper.get_animal_id(url.query) for url in urls}
    assert len(ids_set) == len(urls)


# TODO: Add a test DBHandler using a fixture.
def test_run_web_scraper_small(betamax_session: requests.Session, mocker: MockerFixture):
    """
    Test the whole workflow of Zoo Prague lexicon web scraper.

    It uses a test DBHandler which uses local filesystem.

    Function :func:`scrapers.zoo_scraper.get_animal_urls` is mocked since it returns too many animals.

    Args:
        betamax_session (requests.Session): [description]
        mocker (MockerFixture): A fixture of pytest_mock.
    """
    sleep_time: float = 5
    get_animal_id_spy = mocker.spy(zoo_scraper, 'get_animal_id')

    # Patch the get_animal_urls function
    urls: list[str] = [
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=320-zelva-obrovska&start=320",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=39-zelva-ostnita&start=39",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=321-zelva-pardali&start=321",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=496-sova-palena&start=496",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=643-tygr-ussurijsky&start=643",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=306-tucnak-humboldtuv&start=306",
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=100-bezhrbi-velbloudi&start=100"
    ]
    urls: list[ParseResult] = [urlparse(url) for url in urls]
    mocker.patch('scrapers.zoo_scraper.get_animal_urls', return_value=urls)

    # Patch time.sleep function
    ## Can't patch time.sleep by just always returning True because time.sleep is used in calls a lot by the system with times around 0.005. Mocking it that way caused CPU overheating
    ## The way this works is that the sleep_lambda is called and if argument is lower than sleep_time then original time.sleep function is executed
    unmocked_sleep = time.sleep
    sleep_lambda = lambda secs: True if (sleep_time - 2 <= secs <= sleep_time) else unmocked_sleep(secs)
    mocker.patch('time.sleep', new=sleep_lambda)

    # Act
    output: list[AnimalData] = list()
    zoo_scraper.run_web_scraper(betamax_session, TestHandler(output), sleep_time)

    # Assert
    assert get_animal_id_spy.call_count == len(urls)
    assert len(output) == len(urls)

    pass

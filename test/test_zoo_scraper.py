from betamax_serializers.pretty_json import PrettyJSONSerializer
import betamax
import requests
import pytest
import time
from pytest_mock.plugin import MockerFixture
import os
from urllib.parse import urlparse, ParseResult
import scrapers.zoo_scraper as zoo_scraper
from fixtures.fixtures import BaseTestHandler
from server_dataclasses.models import AnimalData
from pathlib import Path
from fixtures.utils import compare_lists

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

def test_run_web_scraper_pavilon_animals(betamax_session: requests.Session, mocker: MockerFixture):
    """
    Test the whole workflow of Zoo Prague lexicon web scraper. Tests animals that are in zoo houses, not in animal pens.

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
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=27-agama-stepni&start=27",             # Pavilon šelem a plazů
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=795-agama-zapadoafricka&start=795",    # Afrika zblizka
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=140-chameleon-obrovsky&start=140",     # Pavilon velkých želv
        "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat?d=702-kakadu-palmovy&start=702",         # Rákosův pavilon
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
    # List of animal_pens results the method needs
    find_res: dict[str, list] = {
        'zoo_parts': [
            {"_id" : 0, "name" : "Pavilon šelem a plazů", 'is_building': True},
            {"_id" : 1, "name" : "Afrika zblízka", 'is_building': True},
            {"_id" : 2, "name" : "Pavilon velkých želv", 'is_building': True},
            {"_id" : 3, "name" : "Rákosův pavilon", 'is_building': True}
        ]
    }

    output: list[dict] = list()
    zoo_scraper.run_web_scraper(betamax_session, db_handler=BaseTestHandler(output, find_res), min_delay=sleep_time, collection_name="tmp")
    output: list[AnimalData] = [AnimalData(**d) for d in output]

    # Assert
    assert get_animal_id_spy.call_count == len(urls)
    assert len(output) == len(urls)

    assert all([len(animal.map_locations) == 1 for animal in output])

    # Each animal has a map_location which is the same as its index in the output
    assert all([animal.map_locations[0]['_id'] == index for index, animal in enumerate(output)])

def test_run_web_scraper_basic(betamax_session: requests.Session, mocker: MockerFixture):
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
    # List of animal_pens results the method needs
    find_res: dict[str, list] = {
        'animal_pens': [
            {"_id": 0, "name": "želvy", "singular_names": ["želva"]},
            {"_id": 1, "name": "želvy obrovské", "singular_names": ["želva obrovská"]},
            {"_id": 2, "name": "sovy", "singular_names": ["sova"]},
            {"_id": 3, "name": "sovy", "singular_names": ["sova"]},
            {"_id": 4, "name": "tygři, tučňáci", "singular_names": ["tygr", "tučňák"]}
        ]
    }

    output: list[dict] = list()
    zoo_scraper.run_web_scraper(betamax_session, db_handler=BaseTestHandler(output, find_res), min_delay=sleep_time, collection_name="tmp")
    output: list[AnimalData] = [AnimalData(**d) for d in output]

    # Assert
    assert get_animal_id_spy.call_count == len(urls)
    assert len(output) == len(urls)

    zelva_obrovska: AnimalData = next(filter(lambda animal: 'želva obrovská' in animal.name.lower(), output), None)
    assert compare_lists([loc['_id'] for loc in zelva_obrovska.map_locations], [1])

    zelva_ostni: AnimalData = next(filter(lambda animal: 'želva ostnitá' in animal.name.lower(), output), None)
    assert compare_lists([loc['_id'] for loc in zelva_ostni.map_locations], [0])

    zelva_pardali: AnimalData = next(filter(lambda animal: 'želva pardálí' in animal.name.lower(), output), None)
    assert compare_lists([loc['_id'] for loc in zelva_pardali.map_locations], [0])

    sova: AnimalData = next(filter(lambda animal: 'sova' in animal.name.lower(), output), None)
    assert compare_lists([loc['_id'] for loc in sova.map_locations], [2,3])

    tygr: AnimalData = next(filter(lambda animal: 'tygr' in animal.name.lower(), output), None)
    assert tygr.is_currently_available
    assert tygr.sizes == ''
    assert tygr.reproduction == ''
    assert tygr.about_placement_in_zoo_prague is None
    assert tygr.location_in_zoo is None
    assert tygr.food_detail is None
    assert compare_lists([loc['_id'] for loc in tygr.map_locations], [4])

    alpaka: AnimalData = next(filter(lambda animal: 'alpaka' in animal.name.lower(), output), None)
    assert not alpaka.is_currently_available
    assert len(alpaka.map_locations) == 0

    pass

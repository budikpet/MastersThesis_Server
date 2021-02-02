from betamax_serializers.pretty_json import PrettyJSONSerializer
import betamax
import requests
import pytest
from flexmock import flexmock
import os
from urllib.parse import ParseResult
import scrapers.zoo_scraper as zoo_scraper

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
    urls: list[ParseResult] = [url for url in zoo_scraper.get_animal_urls(betamax_session)]

    assert len(urls) == 800
    assert None not in urls
    assert all([url.query != '' for url in urls])

    # Check if IDs of animals contain duplicates
    ids_set: set[int] = {zoo_scraper.get_animal_id(url.query) for url in urls}
    assert len(ids_set) == len(urls)

def test_run_web_scraper(betamax_session: requests.Session):
    zoo_scraper.run_web_scraper(betamax_session, None, 20)
    assert False

    print("Done")

def test_main(mocker):
    """
    Test only the immediate main method, not the whole flow (i. e. make DataCollector which returns immediately).
    """
    # TODO Implement

    # Check raised exceptions from wrong config
    pass
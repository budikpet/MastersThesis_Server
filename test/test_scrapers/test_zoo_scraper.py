from betamax_serializers.pretty_json import PrettyJSONSerializer
import betamax
import requests
import pytest
import os
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
    urls: list[str] = zoo_scraper.get_animal_urls(betamax_session)

    assert len(urls) == 800

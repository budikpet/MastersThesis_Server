from fastapi.testclient import TestClient
from rest.main import app
import pytest
from server_dataclasses.rest_models import AnimalsResult, Metadata, BaseResult, AnimalDataOutput
from rest.config import get_settings
from fixtures.fixtures import BaseTestHandler
from types import SimpleNamespace
from datetime import datetime
from fixtures.utils import compare_lists

client = TestClient(app)
handler = BaseTestHandler
metadata: dict = {
    '_id': 0,
    'next_update': datetime.now(),
    'last_update_start': datetime.now(),
    'last_update_end': datetime.now(),
    'scheduler_state': 0
}

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {'status': 'FastAPI application running.'}

def test_animals_all():
    animals_data = [AnimalDataOutput(_id=0, is_currently_available=True).dict(), AnimalDataOutput(_id=1, is_currently_available=False).dict()]
    for animal_data in animals_data:
        animal_data['_id'] = animal_data.pop('id')

    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': animals_data
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/animals?include_currently_unavailable=True")
    response_data: dict = response.json()
    
    # Assert
    assert response.status_code == 200
    assert len(response_data['data']) == len(find_res['animals_data'])
    assert compare_lists(response_data['data'], find_res['animals_data'], key=lambda obj: obj['_id'])

def test_animals_only_available():
    animals_data = [AnimalDataOutput(_id=0, is_currently_available=True).dict(), AnimalDataOutput(_id=1, is_currently_available=False).dict()]
    for animal_data in animals_data:
        animal_data['_id'] = animal_data.pop('id')

    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': animals_data
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/animals")
    response_data: dict = response.json()
    animals_out: list = [animal for animal in animals_data if animal['is_currently_available'] == True]
    
    # Assert
    assert response.status_code == 200
    assert len(response_data['data']) == 1
    assert compare_lists(response_data['data'], animals_out, key=lambda obj: obj['_id'])

def test_animal_ok():
    animals_data = [AnimalDataOutput(_id=0, is_currently_available=True).dict(), AnimalDataOutput(_id=1, is_currently_available=False).dict()]
    for animal_data in animals_data:
        animal_data['_id'] = animal_data.pop('id')

    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': animals_data
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/animals/0")
    response_data: dict = response.json()
    
    # Assert
    assert response.status_code == 200
    assert len(response_data['data']) == 1
    assert response_data['data'][0].get('_id') == 0

def test_animal_missing():
    animals_data = [AnimalDataOutput(_id=0, is_currently_available=True).dict(), AnimalDataOutput(_id=1, is_currently_available=False).dict()]
    for animal_data in animals_data:
        animal_data['_id'] = animal_data.pop('id')

    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': animals_data
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/animals/10")
    response_data: dict = response.json()
    
    # Assert
    assert response.status_code == 404

def test_animal_missing_by_availability():
    animals_data = [AnimalDataOutput(_id=0, is_currently_available=True).dict(), AnimalDataOutput(_id=1, is_currently_available=False).dict()]
    for animal_data in animals_data:
        animal_data['_id'] = animal_data.pop('id')

    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': animals_data
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/animals/1?include_currently_unavailable=False")
    response_data: dict = response.json()
    
    # Assert
    assert response.status_code == 404

def test_foods():
    find_res: dict[str, list] = {
        'metadata': [metadata],
        'animals_data': [
            {'_id': 0, 'food': 'Trees'},
            {'_id': 1, 'food': 'carcasses'},
            {'_id': 2, 'food': 'small People'}
        ]
    }
    output: list = list()
    res = {
        'handler_class': handler,
        'config_data': {
            'output': output,
            'find_output': find_res
        }
    }
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(**res)

    # Act
    response = client.get("/api/foods")
    response_data: dict = response.json()
    
    # Assert
    data_res = ['Trees', 'Carcasses', 'Small people']
    assert response.status_code == 200
    assert len(response_data['data']) == len(data_res)
    assert compare_lists(response_data['data'], data_res)
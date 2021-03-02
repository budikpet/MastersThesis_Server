from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
import os
from pathlib import Path
from server_dataclasses.interfaces import DBHandlerInterface
import boto3
from botocore.exceptions import ClientError
from .config import get_settings
from types import SimpleNamespace
from server_dataclasses.rest_models import AnimalsResult, Metadata, BaseResult, AnimalDataOutput

api_router = APIRouter(prefix='/api')

@api_router.get('/animals', response_model=AnimalsResult)
async def animals(only_currently_available: bool = True, settings: SimpleNamespace = Depends(get_settings)):
    """
    Return information about all animals that live in Zoo Prague.
    """
    with settings.handler_class(**settings.config_data) as db_handler:
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')[0]
        filter_ = {'is_currently_available': True} if only_currently_available else {}
        data: list[dict] = db_handler.find(filter_, collection_name='animals_data')
        data: list[AnimalDataOutput] = [AnimalDataOutput(**d) for d in data]

    res = AnimalsResult(metadata=Metadata(**metadata),data=data)
    return res

@api_router.get('/animals/{animal_id}', response_model=AnimalsResult)
async def animals(animal_id: int, only_currently_available: bool = True, settings: SimpleNamespace = Depends(get_settings)):
    """
    Return information about an animal of a specific ID.
    """
    with settings.handler_class(**settings.config_data) as db_handler:
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')[0]
        filter_ = {'is_currently_available': True, '_id': animal_id} if only_currently_available else {'_id': animal_id}
        data: list[dict] = db_handler.find(filter_, collection_name='animals_data')
        data: list[AnimalDataOutput] = [AnimalDataOutput(**d) for d in data]
    
    res = AnimalsResult(metadata=Metadata(**metadata),data=data)
    return res

@api_router.get('/classes', response_model=BaseResult)
async def classes(settings: SimpleNamespace = Depends(get_settings)):
    """
    Return a list of zoological classes that animals from Zoo Prague are grouped under.
    """
    with settings.handler_class(**settings.config_data) as db_handler:
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')[0]
        data: list[dict] = db_handler.find({}, projection={'class_': 1}, collection_name='animals_data')
        data: set[str] = {d['class_'].capitalize() for d in data}

    return BaseResult(metadata=Metadata(**metadata),data=data)

@api_router.get('/biotops', response_model=BaseResult)
async def biotops(settings: SimpleNamespace = Depends(get_settings)):
    """
    Return a list of biotops that animals from Zoo Prague usually live in.
    """
    with settings.handler_class(**settings.config_data) as db_handler:
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')[0]
        data: list[dict] = db_handler.find({}, projection={'biotop': 1}, collection_name='animals_data')
        data: set[str] = {d['biotop'].capitalize() for d in data}

    return BaseResult(metadata=Metadata(**metadata),data=data)

@api_router.get('/foods', response_model=BaseResult)
async def foods(settings: SimpleNamespace = Depends(get_settings)):
    """
    Return a list of foods that animals eat.
    """
    with settings.handler_class(**settings.config_data) as db_handler:
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')[0]
        data: list[dict] = db_handler.find({}, projection={'food': 1}, collection_name='animals_data')
        data: set[str] = {d['food'].capitalize() for d in data}

    return BaseResult(metadata=Metadata(**metadata),data=data)

@api_router.get('/mapdata',responses={
        200: {
            'content': {'application/octet-stream': {}},
            'description': 'Successful response',
        }
    })
async def map_data(settings: SimpleNamespace = Depends(get_settings)):
    """
    Return the current version of MBTiles file containing vector maps used by a map library.
    """
    file_prefix: str = settings.map_file_prefix
    filename: str = f'{file_prefix}.mbtiles'
    mbtiles_path = Path(f'./tmp/{file_prefix}/{filename}')

    if(not mbtiles_path.is_file()):
        # Download & cache mbtiles file
        os.makedirs(mbtiles_path.parent, exist_ok=True)
        client = boto3.client('s3')
        client.download_file(settings.aws_storage_bucket_name, filename, mbtiles_path)

    return FileResponse(mbtiles_path, media_type='application/octet-stream', filename=filename)
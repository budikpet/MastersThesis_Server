from functools import lru_cache
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
import os
from pathlib import Path
from server_dataclasses.interfaces import DBHandlerInterface
import boto3
from botocore.exceptions import ClientError
from .config import ApiSettings
from server_dataclasses.models import AnimalData

api_router = APIRouter(prefix='/api')

# @lru_cache()
def get_settings() -> ApiSettings:
    return ApiSettings()

@api_router.get('/animals')
async def animals(only_currently_available: bool = True, settings: ApiSettings = Depends(get_settings)):
    with settings.handler_class(**settings.cfg_dict) as db_handler:
        filter_ = {'is_currently_available': True} if only_currently_available else {}
        animal_data: list[AnimalData] = db_handler.find(filter_, collection_name='zoo_data')
        metadata: dict = db_handler.find({'_id': 0}, collection_name='metadata')

    res = {
        'metadata': metadata,
        'animals': animal_data
    }
    return res

@api_router.get('/mapdata')
async def map_data(settings: ApiSettings = Depends(get_settings)):
    file_prefix: str = settings.map_file_prefix
    filename: str = f'{file_prefix}.mbtiles'
    mbtiles_path = Path(f'./tmp/{file_prefix}/{filename}')

    if(not mbtiles_path.is_file()):
        # Download & cache mbtiles file
        os.makedirs(mbtiles_path.parent, exist_ok=True)
        client = boto3.client('s3')
        client.download_file(settings.aws_storage_bucket_name, filename, mbtiles_path)

    return FileResponse(mbtiles_path, media_type='application/octet-stream', filename=filename)
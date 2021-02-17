from server_dataclasses.interfaces import DBHandlerInterface
from server_dataclasses.models import AnimalData
import json
from pathlib import Path
import os


class JSONTestHandler(DBHandlerInterface):
    """Implementation of a testing DBHandler which uses local filesystem.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)

        if(not os.path.isdir(self.output_dir)):
            os.makedirs(self.output_dir)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return True

    def insert_many(self, data: list, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        for animal in data:
            name = animal.name.replace(' ', '_').lower()
            with (self.output_dir / f"{name}.json").open('w', encoding='utf8') as outfile:  
                json.dump(animal.__dict__, outfile, indent = 4, ensure_ascii=False) 

        return True

    def insert_one(self, data: dict, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        return True

    def update_one(self, filter: dict, data: dict, upsert: bool = False, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """Collects one thing and stores it in a DB."""
        return True

    def rename_collection(self, collection_new_name: str, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        return True

    def drop_collection(self, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        return True

class BaseTestHandler(DBHandlerInterface):
    """Implementation of a testing DBHandler which uses local filesystem.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def __init__(self, output: list[AnimalData]):
        self.output = output

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return True

    def insert_many(self, data: list, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        self.output.extend(data) 

        return True

    def insert_one(self, data: dict, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        self.output.append(data)
        return True

    def update_one(self, filter: dict, data: dict, upsert: bool = False, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """Collects one thing and stores it in a DB."""
        return True

    def rename_collection(self, collection_new_name: str, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        return True

    def drop_collection(self, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        return True

    def find(self, filter_: dict, projection: dict = None, db_name: str = None, collection_name: str = None, **kwargs) -> list[dict]:
        #TODO: Implement?
        pass
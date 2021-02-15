from server_dataclasses.interfaces import DBHandlerInterface
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import os


class MongoDBHandler(DBHandlerInterface):
    """Implementation of a DBHandler which uses remote MongoDB.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def __init__(self, host: str, db_name: str, collection_name: str, **kwargs):
        url = os.getenv('MONGODB_URI', host)
        self.client: MongoClient = MongoClient(url)
        self.db: Database = self.client[db_name]
        self.coll: Collection = self.db[collection_name]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.db, self.coll, self.client = None, None, None

        # suppress errors
        return True

    def insert_many(self, data: list, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]
        
        dicts = [animal.__dict__ for animal in data]
        coll.insert_many(dicts)

        return True

    def insert_one(self, data: dict, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Collects one thing and stores it in a DB.

        Args:
            data (dict): Data to store
            db_name (str, optional): Name of the database where the collection is. Defaults to None.
            collection_name (str, optional): Name of the collection where to put data to. Defaults to None.

        Returns:
            bool: [description]
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        coll.insert_one(data)

        return True

    def update_one(self, filter_: dict, data: dict, upsert: bool = False, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Updates one document. If more then one document is found then only the first is updated.

        Args:
            filter_ (dict): Determines how to find the document to update.
            data (dict): Determines how the document is updated.
            upsert (bool, optional): If set to True and no document is found then a new document is created. Defaults to False.
            db_name (str, optional): Name of the database where the collection is. Defaults to None.
            collection_name (str, optional): Name of the collection where to put data to. Defaults to None.

        Returns:
            bool: [description]
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        coll.update_one(filter_, data, upsert=upsert)

        return True
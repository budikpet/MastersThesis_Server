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

    def insert_many(self, data: list[dict], db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]
        
        coll.insert_many(data)

        return True

    def insert_one(self, data: dict, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Collects one thing and stores it in a DB.

        Args:
            data (dict): Data to store
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection where to put data to. Defaults to the property selected during initialization.

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
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection where to put data to. Defaults to the property selected during initialization.

        Returns:
            bool: [description]
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        coll.update_one(filter_, data, upsert=upsert)

        return True

    def rename_collection(self, collection_new_name: str, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Rename collection.

        Args:
            collection_new_name (str): New name of the collection
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to the property selected during initialization.

        Returns:
            bool: [description]
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        coll.rename(collection_new_name)

        return True

    def drop_collection(self, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Drop collection if it exists.

        Args:
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to the property selected during initialization.

        Returns:
            bool: [description]
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]
        if(coll.name in db.list_collection_names()):
            coll.drop()

        return True

    def find(self, filter_: dict, projection: dict = None, db_name: str = None, collection_name: str = None, **kwargs) -> list[dict]:
        """
        Finds documents in a collection using the defined filter.

        Args:
            filter_ (dict): Defines what kinds of documents are to be found.
            projection (dict, optional): Defines columns which are to be returned. Defaults to the property selected during initialization. and then all columns are returned.
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to the property selected during initialization.

        Returns:
            list[dict]: List of dictionaries which hold document data.
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        return list(coll.find(filter_, projection=projection))

    def collection_exists(self, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Check if the given collection exists.

        Args:
            db_name (str, optional): Name of the database where the collection is. Defaults to the property selected during initialization.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to the property selected during initialization.

        Returns:
            bool: True if the collection exists.
        """
        db: Database = self.db if db_name is None else self.client[db_name]
        coll: Collection = self.coll if collection_name is None else db[collection_name]

        return coll.name in db.list_collection_names()
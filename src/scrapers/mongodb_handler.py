from server_dataclasses.interfaces import DBHandlerInterface
import pymongo


class MongoDBHandler(DBHandlerInterface):
    """Implementation of a DBHandler which uses remote MongoDB.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def __init__(self, host: str, db_name: str, collection_name: str, **kwargs):
        self.client = pymongo.MongoClient(host)
        self.db = self.client[db_name]
        self.coll = self.db[collection_name]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.db, self.coll, self.client = None, None, None

        # suppress errors
        return True

    def insert_many(self, data: list, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        # TODO Implement
        print(f"Ran insert_many for data: '{data}'")

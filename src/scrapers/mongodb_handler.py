from server_dataclasses.interfaces import DBHandlerInterface

class MongoDBHandler(DBHandlerInterface):
    """Implementation of a DBHandler which uses remote MongoDB.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def insert_many(self, data: list) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        #TODO Implement
        print("Ran insert_many")
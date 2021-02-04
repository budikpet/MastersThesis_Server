from server_dataclasses.interfaces import DBHandlerInterface


class TestHandler(DBHandlerInterface):
    """Implementation of a testing DBHandler which uses local filesystem.

    Args:
        DBHandlerInterface ([type]): Interface it implements.
    """

    name: str = 'mongodb'

    def insert_many(self, data: list, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        # TODO Implement
        print(f"Ran insert_many for data: '{data}'")
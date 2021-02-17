import abc
import pkg_resources


class DBHandlerInterface(metaclass=abc.ABCMeta):
    """An interface class for all DBHandler classes (Bridge-pattern classes) which stand between server and concrete DB solution.

    Provides methods that are used by the server.

    Args:
        metaclass ([type], optional): [description]. Defaults to abc.ABCMeta.
    """

    @classmethod
    def name() -> str:
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, subclass):
        demands: list[bool] = [
            hasattr(subclass, '__enter__'),
            callable(subclass.__enter__),
            hasattr(subclass, '__exit__'),
            callable(subclass.__exit__),
            hasattr(subclass, 'update_one'),
            callable(subclass.update_one),
            hasattr(subclass, 'insert_one'),
            callable(subclass.insert_one),
            hasattr(subclass, 'rename'),
            callable(subclass.rename),
            hasattr(subclass, 'drop_collection'),
            callable(subclass.drop_collection),
            hasattr(subclass, 'find'),
            callable(subclass.find),
            hasattr(subclass, 'insert_many'),
            callable(subclass.insert_many)
        ]
        return (False in demands) or NotImplemented

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError

    @abc.abstractmethod
    def insert_many(self, data: list, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """Collects a list and stores it in a DB"""
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
    def update_one(self, filter: dict, data: dict, upsert: bool = False, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
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
        raise NotImplementedError

    @abc.abstractmethod
    def rename_collection(self, collection_new_name: str, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Rename collection.

        Args:
            collection_new_name (str): New name of the collection
            db_name (str, optional): Name of the database where the collection is. Defaults to None.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to None.

        Returns:
            bool: [description]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def drop_collection(self, db_name: str = None, collection_name: str = None, **kwargs) -> bool:
        """
        Drop collection if it exists.

        Args:
            db_name (str, optional): Name of the database where the collection is. Defaults to None.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to None.

        Returns:
            bool: [description]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def find(self, filter_: dict, projection: dict = None, db_name: str = None, collection_name: str = None, **kwargs) -> list[dict]:
        """
        Finds documents in a collection using the defined filter.

        Args:
            filter_ (dict): Defines what kinds of documents are to be found.
            projection (dict, optional): Defines columns which are to be returned. Defaults to None and then all columns are returned.
            db_name (str, optional): Name of the database where the collection is. Defaults to None.
            collection_name (str, optional): Name of the collection which is to be used. Defaults to None.

        Returns:
            list[dict]: List of dictionaries which hold document data.
        """
        raise NotImplementedError


def load_interface_subclasses():
    """
    Uses entry_points from setup.py to load all subclasses of all interfaces specified in this module.
    """
    # print("load_interface_subclasses")
    groups: list[str] = ['masters_thesis_server.db_handlers']
    for group in groups:
        # print(f"Group: [{group}]")
        for ep in pkg_resources.iter_entry_points(group=group):
            # print(f'Name: {ep.name}')
            ep.load()


load_interface_subclasses()

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
            hasattr(subclass, 'insert_many'),
            callable(subclass.insert_many)
        ]
        return (False in demands) or NotImplemented

    @abc.abstractmethod
    def insert_many(self, data: list) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        raise NotImplementedError


class DataCollectorInterface(metaclass=abc.ABCMeta):
    """An interface class for all DataCollector classes that get data from Zoo Prague lexicon and store it in a DB.

    Args:
        metaclass ([type], optional): [description]. Defaults to abc.ABCMeta.
    """

    @classmethod
    def name() -> str:
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'collect_data') and
                callable(subclass.collect_data)) or NotImplemented

    @abc.abstractmethod
    def collect_data(self, db_handler: DBHandlerInterface, **kwargs):
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        raise NotImplementedError


def load_interface_subclasses():
    """
    Uses entry_points from setup.py to load all subclasses of all interfaces specified in this module.
    """
    print("load_interface_subclasses")
    groups: list[str] = ['masters_thesis_server.db_handlers',
                         'masters_thesis_server.data_collectors']
    for group in groups:
        print(f"Group: [{group}]")
        for ep in pkg_resources.iter_entry_points(group=group):
            print(f'Name: {ep.name}')
            ep.load()


load_interface_subclasses()

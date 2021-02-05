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
    def insert_many(self, data: list, **kwargs) -> bool:
        """Collects Zoo Prague lexicon data and stores it in a DB."""
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

import abc


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
    def collect_data(self):
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        raise NotImplementedError


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


# def getDBHandlerSubclasses() -> list[DBHandlerInterface]:
#     """
#     Returns all subclasses of DBHandlerInterface.

#     Returns:
#         list[DBHandlerInterface]: [description]
#     """
#     return DBHandlerInterface.__subclasses__()


# def getDataCollectorSubclasses() -> list[DataCollectorInterface]:
#     """
#     Returns all subclasses of DataCollectorInterface.

#     Returns:
#         list[DataCollectorInterface]: [description]
#     """
#     return DataCollectorInterface.__subclasses__()

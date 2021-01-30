from server_dataclasses.interfaces import DataCollectorInterface, DBHandlerInterface

class OfficialDataCollector(DataCollectorInterface):
    """
    Implementation of a DataCollector which is a web scraper of official Zoo Prague lexicon page [1].

    [1] https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat

    Args:
        DataCollectorInterface ([type]): [description]
    """

    name: str = 'zooPragueOfficialPage'

    def __init__(self, db_handler: DBHandlerInterface):
        self.url = "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat"

    def collect_data(self):
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        pass
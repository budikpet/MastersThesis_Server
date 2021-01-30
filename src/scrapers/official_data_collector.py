from server_dataclasses.interfaces import DataCollectorInterface, DBHandlerInterface

class OfficialDataCollector(DataCollectorInterface):
    """
    Implementation of a DataCollector which is a web scraper of official Zoo Prague lexicon page [1].

    [1] https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat

    Args:
        DataCollectorInterface ([type]): [description]
    """

    name: str = 'zooPragueOfficialPage'

    def collect_data(self, db_handler: DBHandlerInterface, **kwargs):
        """Collects Zoo Prague lexicon data and stores it in a DB."""
        self.url = "https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat"
        self.db_handler = db_handler
        # TODO: Implement
        pass
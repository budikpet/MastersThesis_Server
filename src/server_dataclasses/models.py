from dataclasses import dataclass, field
from enum import IntEnum


@dataclass
class AnimalData():
    """Holds data about animal parsed from Zoo Prague lexicon."""

    ### Parsed data
    _id: int = -1
    name: str = None
    latin_name: str = None

    # Text above the image
    base_summary: str = None
    image: str = None

    # "Třída"
    class_: str = None
    class_latin: str = None

    # "Řád"
    order: str = None
    order_latin: str = None

    # "Rozšíření"
    continent: str = None
    continent_detail: str = None

    biotop: str = None
    biotop_detail: str = None

    # "Potrava"
    food: str = None
    food_detail: str = None

    sizes: str = None
    reproduction: str = None

    # "Zajímavosti"
    interesting_data: str = None

    # "Chov v Zoo Praha"
    about_placement_in_zoo_prague: str = None

    # "Umístění v Zoo Praha"
    location_in_zoo: str = None

    ### Other data

    # False for animals that have an indication in about_placement_in_zoo_prague variable
    is_currently_available: bool = True

    # IDs of locations of the animal's pens in map data
    map_locations: list[str] = field(default_factory=list)

class SchedulerStates(IntEnum):
    # Waiting for update date. If update date is reached then add scraping job and start worker dyno
    WAIT = 0
    # Worker dyno had been started and still has work. 
    UPDATING = 1
    # No work remains for the worker dyno. Stop it and schedule a new update date
    WORK_DONE = 2


class DynoStates(IntEnum):
    DOWN = 0
    UP = 1
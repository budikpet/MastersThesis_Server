from pydantic import BaseModel, Field
from datetime import datetime

class AnimalDataOutput(BaseModel):
    """
    Holds data about animal parsed from Zoo Prague lexicon.

    Used as a response model
    """

    id: int = Field(..., alias='_id')
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
    map_locations: list[str] = list()

class Metadata(BaseModel):
    _id: int = 0
    next_update: datetime
    last_update_start: datetime
    last_update_end: datetime
    scheduler_state: int

class AnimalsResult(BaseModel):
    metadata: Metadata
    animal_data: list[AnimalDataOutput]

class BaseResult(BaseModel):
    metadata: Metadata
    data: list[str]
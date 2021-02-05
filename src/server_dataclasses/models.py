from dataclasses import dataclass, field


@dataclass
class AnimalData():
    """Holds data about animal parsed from Zoo Prague lexicon."""

    # Parsed data
    id: int = -1
    name: str = ''
    latin_name: str = ''

    # Text above the image
    base_summary: str = ''
    image: str = ''

    # "Třída"
    class_: str = ''
    class_latin: str = ''

    # "Řád"
    order: str = ''
    order_latin: str = ''

    # "Rozšíření"
    continent: str = ''
    continent_detail: str = ''

    biotop: str = ''
    biotop_detail: str = ''

    # "Potrava"
    food: str = ''
    food_detail: str = ''

    sizes: str = ''
    reproduction: str = ''

    # "Zajímavosti"
    interesting_data: str = ''

    # "Chov v Zoo Praha"
    about_placement_in_zoo_prague: str = ''

    # "Umístění v Zoo Praha"
    location_in_zoo: str = ''

    # Other data

    # False for animals that have an indication in about_placement_in_zoo_prague variable
    is_currently_available: bool = True

    # IDs of locations of the animal's pens in map data
    map_locations: list[str] = field(default_factory=list)

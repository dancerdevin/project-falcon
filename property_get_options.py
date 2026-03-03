from enum import Enum, auto

class PropertyLocationType(Enum):
  ADDRESS = auto()
  ZIP = auto()
  LATLONG = auto()

class PropertyGetOption(Enum):
  JSON_ONLY = auto()
  JSON_FIRST_THEN_API_NO_UPDATE = auto()
  JSON_FIRST_THEN_API_AND_UPDATE_JSON = auto()
  API_ONLY = auto()
  API_ONLY_AND_JSON_DUMP = auto()

# Divide PropertyGetOptions into distinct and potentially overlapping sublists.

JSON_GET_OPTIONS = [
  PropertyGetOption.JSON_ONLY,
  PropertyGetOption.JSON_FIRST_THEN_API_NO_UPDATE,
  PropertyGetOption.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]

JSON_FIRST_OPTIONS = [
  PropertyGetOption.JSON_FIRST_THEN_API_NO_UPDATE,
  PropertyGetOption.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]

UPDATE_JSON_OPTIONS = [
   PropertyGetOption.API_ONLY_AND_JSON_DUMP,
   PropertyGetOption.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]
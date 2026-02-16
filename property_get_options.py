from enum import Enum, auto

class PropertyGetOptions(Enum):
  JSON_ONLY = auto()
  JSON_FIRST_THEN_API_NO_UPDATE = auto()
  JSON_FIRST_THEN_API_AND_UPDATE_JSON = auto()
  API_ONLY = auto()
  API_ONLY_AND_JSON_DUMP = auto()

# Divide PropertyGetOptions into distinct and potentially overlapping sublists.

JSON_GET_OPTIONS = [
  PropertyGetOptions.JSON_ONLY,
  PropertyGetOptions.JSON_FIRST_THEN_API_NO_UPDATE,
  PropertyGetOptions.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]

JSON_FIRST_OPTIONS = [
  PropertyGetOptions.JSON_FIRST_THEN_API_NO_UPDATE,
  PropertyGetOptions.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]

UPDATE_JSON_OPTIONS = [
   PropertyGetOptions.API_ONLY_AND_JSON_DUMP,
   PropertyGetOptions.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]
from property_data import Property
from typing import List
from property_get_options import PropertyGetOption, PropertyLocationType
from property_provider import *
from property_analyzers import *

# TODO: When I pull data from a database rather than JSON dumps, the analysis should already be done. Check if a PropertyAnalyzer() should be instantiated?
# Or create a new Analyzer for subsets of already-analyzed data stored in the database to gather group-level data about that subset?

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get_property(self, location_type: PropertyLocationType, location: str, option=PropertyGetOption.JSON_ONLY) -> Property:
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    if location_type != PropertyLocationType.ADDRESS:
      raise Exception("request_property() expects an ADDRESS. For ZIP or LATLONG locations, call request_properties().")

    if self.cached_property:
      pass

    property_provider = CompletePropertyProvider()
    prop = property_provider.request_property(location_type=location_type, location=location, option=option)
    return prop
  
  def get_properties(self, location_type: PropertyLocationType, location: str, option=PropertyGetOption.JSON_ONLY) -> List[Property]:
    # TODO: handle ZIP and LATLONG inputs for lists of Properties to, e.g., update database in bulk
    # This should still mostly work, but the analysis functions are pointless. Incorporate locale-level analysis
    raise Exception("Error: PropertyStore.get_properties() called before implementation.")
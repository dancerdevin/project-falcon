from property_data import Property
from typing import List
from property_get_options import PropertyGetOptions
from property_providers import *
from property_analyzers import *

# TODO: When I pull data from a database rather than JSON dumps, the analysis should already be done. Check if a PropertyAnalyzer() should be instantiated?
# Or create a new Analyzer for subsets of already-analyzed data stored in the database to gather group-level data about that subset?

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get_property(self, address, get_option=PropertyGetOptions.JSON_ONLY) -> Property:
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    if self.cached_property:
      pass

    property_provider = CompletePropertyProvider()
    prop = property_provider.request_property(address=address, option=get_option)
    return prop
  
  def get_properties(self, region, get_option=PropertyGetOptions.JSON_ONLY) -> List[Property]:
    # TODO: handle ZIP and lat-long inputs for lists of Properties to, e.g., update database in bulk
    # This should still mostly work, but the analysis functions are pointless
    raise Exception("Error: PropertyStore.get_properties() called before implementation.")
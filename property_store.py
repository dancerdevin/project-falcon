from property_schema import Property
from typing import Protocol
from property_data_intake import rentcast_api, rentometer_api

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""

"""When requesting data on a Property, first check storage."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get(self, location) -> Property:
    # NOTE: This can initially fail by default, then, e.g., scan all JSON dumps saved in the root directory, then get more refined.
    # When it fails, instantiate CompletePropertyProvider and get the Property to return that way
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    # the real point here is to add data validation checks and have some work so let's just do that first
    if self.cached_property:
      pass # ... check if it's the location we're looking for etc then return
    property_provider = CompletePropertyProvider()
    prop = property_provider.request(location)
    return prop

"""Interface that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request(location) -> Property: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object.
  def request(location) -> Property:
    prop = Property()
    rentcast_provider = RentcastPropertyProvider()
    prop = rentcast_provider.request(location)
    rentometer_provider = RentometerPropertyProvider()
    prop = rentometer_provider.request(location)
    if not prop.is_complete():
      raise Exception("Error: Property obj is not complete at the end of CompletePropertyProvider assembly.")
    return prop

class RentcastPropertyProvider:
  # This follows the PropertyProvider Protocol and def request() outputs a partial property object. Put in CompletePropertyProvider
  def request(location) -> Property:
    # TODO: Consider how to use rentcast api here and how to replace build_properties() functionality with new partial objects
    df_from_json = rentcast_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentcast data specifically
    pass

class RentometerPropertyProvider:
  def request(location) -> Property:
    # TODO: Consider how to use rentcast api here and how to replace build_properties() functionality with new partial objects
    df_from_json = rentometer_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentometer data specifically
    pass

if __name__ == "__main__":
  pass
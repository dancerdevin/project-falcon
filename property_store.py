from property_schema import Property
from typing import Protocol
from property_data_intake import rentcast_api, rentometer_api
from property_level_analysis import parse_rentcast_data, add_rent_to_parsed_rentcast_data, add_costs_to_parsed_rentcast_data, build_attributes, build_features, build_location, build_metadata, build_values

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
  def request(self, location) -> Property:
    prop = Property()
    rentcast_provider = RentcastPropertyProvider()
    # TODO: currently a df, not a Property
    rentcast_df = rentcast_provider.request(location)
    rentometer_provider = RentometerPropertyProvider()
    rentometer_df = rentometer_provider.request(location)
    df = add_rent_to_parsed_rentcast_data(rentcast_df, rentometer_df)
    df = add_costs_to_parsed_rentcast_data(df)
    # NOTE: currently copied from property_level_analysis.build_properties()
    prop_list = []

    for row in df.itertuples(index=False):
        location_details = build_location(row)
        feature_details = build_features(row)
        attribute_details = build_attributes(row)
        value_details = build_values(row)
        metadata = build_metadata(row)
        prop_list.append(Property(location_details, feature_details, attribute_details, value_details, metadata))

    print(f"Prop_list: {prop_list}")

    prop = prop_list[0]
    if not prop.is_complete():
      raise Exception("Error: Property obj is not complete at the end of CompletePropertyProvider assembly.")
    return prop

class RentcastPropertyProvider:
  # This follows the PropertyProvider Protocol and def request() outputs a partial property object. Put in CompletePropertyProvider
  # TODO: CURRENTLY RETURNS DF, NOT PARTIAL PROPERTY. So first, do work needed with DF for a given API call, add to Property, and AT THE END, analysis.
  def request(self, location) -> Property:
    # TODO: Consider how to use rentcast api here and how to replace build_properties() functionality with new partial objects
    df_from_json = rentcast_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentcast data specifically
    rentcast_subset_df = parse_rentcast_data(df_from_json)
    return rentcast_subset_df

class RentometerPropertyProvider:
  # TODO: CURRENTLY RETURNS DF, NOT PARTIAL PROPERTY. 
  def request(self, location) -> Property:
    # TODO: Consider how to use rentcast api here and how to replace build_properties() functionality with new partial objects
    df_from_json = rentometer_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentometer data specifically
    return df_from_json

if __name__ == "__main__":
  # Test address: '5214 S Thompson Ave, Tacoma, WA 98408'
  prop_store = PropertyStore()
  prop = prop_store.get("5214 S Thompson Ave, Tacoma, WA 98408")
  print(prop)
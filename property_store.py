from property_schema import Property, PropertyData, LocationDetails, FeatureDetails, AttributeDetails, ValueDetails, Metadata
from typing import Protocol, List
from property_data_intake import rentcast_api, rentometer_api
from property_level_analysis import parse_rentcast_data, add_rent_to_parsed_rentcast_data, add_costs_to_parsed_rentcast_data # , build_attributes, build_features, build_location, build_metadata, build_values

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""

"""When requesting data on a Property, first check storage."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get(self, location) -> List[Property]:
    # NOTE: This can initially fail by default, then, e.g., scan all JSON dumps saved in the root directory, then get more refined.
    # When it fails, instantiate CompletePropertyProvider and get the Property to return that way
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    # the real point here is to add data validation checks and have some work so let's just do that first
    if self.cached_property:
      pass # ... check if it's the location we're looking for etc then return
    property_provider = CompletePropertyProvider()
    prop_list = property_provider.request(location)
    return prop_list

"""Interface for intake that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request(location) -> List[Property]: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop_list: List[Property]) -> List[Property]: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object.
  def request(self, location) -> List[Property]:
    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop_list = rentcast_provider.request(location)
    for prop in rentcast_prop_list:
      if prop.location.street_address == "6478 S M St, Tacoma, WA 98408":
        print("address found from RentcastProvider")
        print(prop)
    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop_list = rentometer_provider.request(location)
    all_prop_data = rentcast_prop_list + rentometer_prop_list
    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)
    # TODO: also update analyzer to handle a list of properties
    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop_list = combined_prop_analyzer.analyze(combined_prop_list)
    for prop in analyzed_prop_list:
      if prop.location.street_address == "6478 S M St, Tacoma, WA 98408":
        print("address found in analyzed_prop_list")
        print(prop)
    return analyzed_prop_list


class RentcastPropertyProvider:
  """This follows the PropertyProvider Protocol and def request() outputs a partial property object."""
  def request(self, location) -> List[Property]:
    # TODO: check IF the information is available saved, and if not call the API for real, instead of calling the function but actually intake "from_json_dump"
    rentcast_df = rentcast_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentcast data specifically
    rentcast_subset_df = parse_rentcast_data(rentcast_df)
    # TODO: depreciate this part of the second analysis function
    rentcast_subset_df = rentcast_subset_df.rename(columns={"formattedAddress": "street_address", "value": "value_est"})
    # TODO: actually get this from the Rentcast API finally
    rentcast_subset_df["rentcast_url"] = "placeholder"
    prop_list = PropertyData.build_properties_from_dataframe(rentcast_subset_df)
    return prop_list

class RentometerPropertyProvider:
  def request(self, location) -> List[Property]:
    rentometer_df = rentometer_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentometer data specifically
    rentometer_df = rentometer_df[["address", "mean", "median", "min", "max", "quickview_url"]].reset_index(drop=True)
    rentometer_df = rentometer_df.rename(columns={"quickview_url": "rentometer_url"})
    rentometer_df = rentometer_df.drop_duplicates()

    rentometer_df = rentometer_df.rename(columns={
      "address": "street_address",
      "mean": "mean_rent_est",
      "median": "median_rent_est",
      "min": "min_rent",
      "max": "max_rent"})
    
    # Check if the address exists
    exists = (rentometer_df['street_address'] == '6478 S M St, Tacoma, WA 98408').any()
    print(f"Address found in rentometer_df: {exists}")

    prop_list = PropertyData.build_properties_from_dataframe(rentometer_df)
    for prop in prop_list:
      if prop.location.street_address == '6478 S M St, Tacoma, WA 98408':
        print("it's also in prop_list!")
    return prop_list

class CompletePropertyAnalyzer:
  """Include analysis that requires, e.g., data from both Rentcast and Rentometer."""
  def analyze(self, prop_list: List[Property]) -> List[Property]:
    if not isinstance(prop_list, list):
      raise TypeError("CompletePropertyAnalyzer takes a list of Properties. Please input the result of at least one different PropertyProvider.")
    # TODO: make it so partial data is just skipped rather than errors out
    # if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
    #   raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    prop_big_df = PropertyData.prop_list_to_dataframe(prop_list)
    analyzed_df = add_costs_to_parsed_rentcast_data(prop_big_df)
    analyzed_prop_list = PropertyData.build_properties_from_dataframe(analyzed_df)
    return analyzed_prop_list

if __name__ == "__main__":
  # Test address: '5214 S Thompson Ave, Tacoma, WA 98408'
  # another test address: "6478 S M St, Tacoma, WA 98408"
  prop_store = PropertyStore()
  prop_list = prop_store.get("6478 S M St, Tacoma, WA 98408")
  for prop in prop_list:
    if prop.location.street_address == "6478 S M St, Tacoma, WA 98408":
      print(prop)
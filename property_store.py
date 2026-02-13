from property_schema import Property, PropertyData
from typing import Protocol, List
from property_level_analysis import parse_rentcast_data, add_costs_to_parsed_rentcast_data
from property_intake_clients import RentcastAPIClient, RentometerAPIClient
from enum import Enum, auto
from json_loading import json_to_df_from_disk
from pandas import DataFrame

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""
class PropertyGetOptions(Enum):
  JSON_ONLY = auto()
  JSON_FIRST_THEN_API_NO_UPDATE = auto()
  JSON_FIRST_THEN_API_AND_UPDATE_JSON = auto()
  API_ONLY = auto()
  API_ONLY_AND_JSON_DUMP = auto()

JSON_GET_OPTIONS = [
  PropertyGetOptions.JSON_ONLY,
  PropertyGetOptions.JSON_FIRST_THEN_API_NO_UPDATE,
  PropertyGetOptions.JSON_FIRST_THEN_API_AND_UPDATE_JSON
]

# TODO: 1) change APIClient functionality so API_ONLY/JSON_FIRST_THEN_API_NO_UPDATE and API_ONLY_JSON_DUMP/JSON_FIRSTblahblah replace save_to_disk stuff
# 2) JSON_FIRST options actually have fall-through code (simulate then test)
# 3) depreciate VALID_OPTIONS and add basic PropertyPublish code/interface for complete circuit again

"""When requesting data on a Property, first check storage."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get(self, location, get_option=PropertyGetOptions.JSON_ONLY) -> List[Property]:
    # NOTE: This can initially fail by default, then, e.g., scan all JSON dumps saved in the root directory, then get more refined.
    # When it fails, instantiate CompletePropertyProvider and get the Property to return that way
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    # the real point here is to add data validation checks and have some work so let's just do that first
    if self.cached_property:
      pass # ... check if it's the location we're looking for etc then return
    option = ""
    if get_option == PropertyGetOptions.JSON_ONLY:
      option = PropertyGetOptions.JSON_ONLY
    if not option:
      raise Exception("Error: option string was not set from get_option parameter.")

    property_provider = CompletePropertyProvider()
    prop_list = property_provider.request(location=location, option=option)
    return prop_list

"""Interface for intake that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request(location, option) -> List[Property]: ...

  def _parse(self, df: DataFrame) -> DataFrame: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop_list: List[Property]) -> List[Property]: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object.
  def request(self, location, option) -> List[Property]:
    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop_list = rentcast_provider.request(location=location, option=option)
    for prop in rentcast_prop_list:
      if prop.location.street_address == "6478 S M St, Tacoma, WA 98408":
        print("address found from RentcastProvider")
        print(prop)
    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop_list = rentometer_provider.request(location=location, option=option)
    all_prop_data = rentcast_prop_list + rentometer_prop_list
    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)
    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop_list = combined_prop_analyzer.analyze(combined_prop_list)
    for prop in analyzed_prop_list:
      if prop.location.street_address == "6478 S M St, Tacoma, WA 98408":
        print("address found in analyzed_prop_list")
        print(prop)
    return analyzed_prop_list


class RentcastPropertyProvider:
  """This follows the PropertyProvider Protocol and def request() outputs a partial property object."""
  def request(self, location, option) -> List[Property]:
    # TODO: check IF the information is available saved, and if not call the API for real, instead of calling the function but actually intake "from_json_dump"
    if option in JSON_GET_OPTIONS:
      rentcast_df = json_to_df_from_disk("rentcast", "")
    else:
      rentcast_df = RentcastAPIClient().fetch(location=location, option=option)

    rentcast_subset_df = self._parse(rentcast_df)

    prop_list = PropertyData.build_properties_from_dataframe(rentcast_subset_df)
    return prop_list
  
  def _parse(self, df: DataFrame) -> DataFrame:
    df = parse_rentcast_data(df)
    df = df.rename(columns={
      "formattedAddress": "street_address",
      "value": "value_est",
      "zipCode": "zip_code",
      "squareFootage": "sqft",
      "propertyType": "property_type",
      "lotSize": "lot_size",
      "yearBuilt": "year_built",
      "assessorID": "assessor_ID",
      "legalDescription": "legal_description",
      "ownerOccupied": "owner_occupied"})
    
    # TODO: actually get this from the Rentcast API finally
    df["rentcast_url"] = "placeholder"
    return df
    

class RentometerPropertyProvider:
  def request(self, location, option) -> List[Property]:
    if option in JSON_GET_OPTIONS:
      rentometer_df = json_to_df_from_disk("rentometer", "")
    else:
      rentometer_df = RentometerAPIClient().fetch(location=location, option=option)

    rentometer_df = self._parse(rentometer_df)

    prop_list = PropertyData.build_properties_from_dataframe(rentometer_df)
    return prop_list
  
  def _parse(self, df: DataFrame) -> DataFrame:
    df = df[["address", "mean", "median", "min", "max", "quickview_url"]].reset_index(drop=True)
    df = df.drop_duplicates()

    df = df.rename(columns={
      "quickview_url": "rentometer_url",
      "address": "street_address",
      "mean": "mean_rent_est",
      "median": "median_rent_est",
      "min": "min_rent",
      "max": "max_rent"})
    
    return df

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
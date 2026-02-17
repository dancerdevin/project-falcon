from property_schema import Property, PropertyData
from typing import Protocol, List
from property_level_analysis import parse_rentcast_data, add_costs_to_parsed_rentcast_data
from property_intake_clients import RentcastAPIClient, RentometerAPIClient
from property_get_options import PropertyGetOptions, JSON_GET_OPTIONS, JSON_FIRST_OPTIONS
from json_loading import json_to_df_from_disk
from property_intake_func import find_location_matches_in_cleaned_df
from pandas import DataFrame


# TODO: When I pull data from a database rather than JSON dumps, the analysis should already be done. Check if a PropertyAnalyzer() should be instantiated?
# Or create a new Analyzer for subsets of already-analyzed data stored in the database to gather group-level data about that subset?

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""
class PropertyStore:
  def __init__(self):
    self.cached_property = None

  def get(self, location, get_option=PropertyGetOptions.JSON_ONLY) -> List[Property]:
    # TODO: simple initial circuit: on init no "stored_property", load JSON files on disk, provide Property, store Property for 2nd call?
    # the real point here is to add data validation checks and have some work so let's just do that first
    if self.cached_property:
      pass # ... check if it's the location we're looking for etc then return

    property_provider = CompletePropertyProvider()
    prop_list = property_provider.request(location=location, option=get_option)
    return prop_list

"""Interface for intake that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request(location, option) -> List[Property]: ...

  def _clean(self, df: DataFrame) -> DataFrame: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop_list: List[Property]) -> List[Property]: ...

class CompletePropertyProvider:
  """List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object."""
  def request(self, location, option) -> List[Property]:
    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop_list = rentcast_provider.request(location=location, option=option)

    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop_list = rentometer_provider.request(location=location, option=option)

    # TODO: more elegant or explicit way of collecting all provided data
    all_prop_data = rentcast_prop_list + rentometer_prop_list
    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)

    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop_list = combined_prop_analyzer.analyze(combined_prop_list)

    return analyzed_prop_list


class RentcastPropertyProvider:
  """This follows the PropertyProvider Protocol and def request() outputs a partial property object."""
  def request(self, location, option) -> List[Property]:
    rentcast_df = DataFrame()

    if option in JSON_GET_OPTIONS:
      rentcast_df = json_to_df_from_disk("rentcast", "")
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, location)
      print(f"Number of rows in rentcast_df after JSON location match check: {len(rentcast_df)}")

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentcast_df.empty): # Encompass 1) fall-through for JSON-first or 2) API call only.
      rentcast_df = RentcastAPIClient().fetch(location=location, option=option)
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, location)
      print(f"Number of rows in rentcast_df after API location match check: {len(rentcast_df)}")

    if rentcast_df.empty:
      print("Warning: No properties associated with that location could be found in the Rentcast data.")

    prop_list = PropertyData.build_properties_from_dataframe(rentcast_df)
    return prop_list
  
  def _clean(self, df: DataFrame) -> DataFrame:
    df = parse_rentcast_data(df)
    df = df.rename(columns={
      "id": "rentcast_id",
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
    
    return df
    

class RentometerPropertyProvider:
  def request(self, location, option) -> List[Property]:
    if option in JSON_GET_OPTIONS:
      rentometer_df = json_to_df_from_disk("rentometer", "")
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)
      print(f"Number of rows in rentometer_df after JSON location match check: {len(rentometer_df)}")

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentometer_df.empty):
      rentometer_df = RentometerAPIClient().fetch(location=location, option=option)
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)
      print(f"Number of rows in rentometer_df after API location match check: {len(rentometer_df)}")

    prop_list = PropertyData.build_properties_from_dataframe(rentometer_df)
    return prop_list
  
  def _clean(self, df: DataFrame) -> DataFrame:
    df = df[["address", "mean", "median", "min", "max", "quickview_url", "rentometer_filename"]].reset_index(drop=True)
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
    # TODO: make it so partial data is just skipped rather than errors out (change in add_costs functionality / move here?). Also no rentcast_url, just rentcast_id
    # if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
    #   raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    prop_big_df = PropertyData.prop_list_to_dataframe(prop_list)
    analyzed_df = add_costs_to_parsed_rentcast_data(prop_big_df)
    analyzed_prop_list = PropertyData.build_properties_from_dataframe(analyzed_df)
    return analyzed_prop_list
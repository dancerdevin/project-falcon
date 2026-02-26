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

"""Interface for intake that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request_property(location, option) -> Property: ...

  def _clean(self, df: DataFrame) -> DataFrame: ...

class PropertiesProvider(Protocol):
  def request_properties(location, option) -> List[Property]: ...

  def _clean(self, df: DataFrame) -> DataFrame: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop_list: List[Property]) -> List[Property]: ...

class CompletePropertyProvider:
  """List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object."""
  def request_property(self, address, option) -> Property:
    all_prop_data = []

    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop = rentcast_provider.request_property(address=address, option=option)
    print(f"Rentcast prop: {rentcast_prop}")
    all_prop_data.append(rentcast_prop)

    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop = rentometer_provider.request_property(location=address, option=option)
    print(f"Rentometer prop: {rentometer_prop}")
    all_prop_data.append(rentometer_prop)
    print(all_prop_data)

    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)
    # NOTE: combine_partial_prop_data() still returns List[Property].
    if len(combined_prop_list) > 1:
      raise Exception("Error: combined_prop_list contains more than 1 element. Multiple addresses were likely detected.")
    combined_prop = combined_prop_list[0]

    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop = combined_prop_analyzer.analyze_property(combined_prop)

    return analyzed_prop

class CompletePropertiesProvider:
  """List distinct PropertyProviders and go through them as needed. This will return a completely initialized List of Property objects."""
  # TODO: Implement to work with PropertyStore.get_properties()
  def request_properties(self, location, option) -> List[Property]:
    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop_list = rentcast_provider.request_property(address=location, option=option)

    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop_list = rentometer_provider.request_properties(location=location, option=option)

    # TODO: more elegant or explicit way of collecting all provided data
    all_prop_data = rentcast_prop_list + rentometer_prop_list
    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)

    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop_list = combined_prop_analyzer.analyze_properties(combined_prop_list)

    return analyzed_prop_list

class RentcastPropertyProvider:
  """This follows the PropertyProvider Protocol and def request() outputs a partial property object."""
  def request_property(self, address, option) -> Property:
    rentcast_df = DataFrame()

    if option in JSON_GET_OPTIONS:
      rentcast_df = json_to_df_from_disk("rentcast", "")
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, address)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentcast_df.empty): # Encompass 1) fall-through for JSON-first or 2) API call only.
      rentcast_df = RentcastAPIClient().fetch(location=address, option=option)
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, address)

    if rentcast_df.empty:
      print("Warning: No properties associated with that location could be found in the Rentcast data.")

    prop = PropertyData.build_property_from_dataframe(rentcast_df)
    return prop
  
  def request_properties(self, region, option) -> List[Property]:
    rentcast_df = DataFrame()

    if option in JSON_GET_OPTIONS:
      rentcast_df = json_to_df_from_disk("rentcast", "")
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, region)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentcast_df.empty): # Encompass 1) fall-through for JSON-first or 2) API call only.
      rentcast_df = RentcastAPIClient().fetch(location=region, option=option)
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(rentcast_df, region)

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
  def request_property(self, location, option) -> Property:
    if option in JSON_GET_OPTIONS:
      rentometer_df = json_to_df_from_disk("rentometer", "")
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentometer_df.empty):
      rentometer_df = RentometerAPIClient().fetch(location=location, option=option)
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)

    # NOTE: Rentometer specifically may give different estimations for the same address at different times. For now, just take last row.
    if len(rentometer_df) > 1:
      rentometer_df = rentometer_df.iloc[[-1]]

    prop = PropertyData.build_property_from_dataframe(rentometer_df)
    return prop

  def request_properties(self, location, option) -> List[Property]:
    if option in JSON_GET_OPTIONS:
      rentometer_df = json_to_df_from_disk("rentometer", "")
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentometer_df.empty):
      rentometer_df = RentometerAPIClient().fetch(location=location, option=option)
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(rentometer_df, location)

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
  # TODO: def __init__() valid data sources dict so you can complete todo below
  def analyze_property(self, prop: Property) -> Property:
    # TODO: make it so partial data is just skipped rather than errors out (change in add_costs functionality / move here?). Also no rentcast_url, just rentcast_id
    # if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
    #   raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    analyzed_df = add_costs_to_parsed_rentcast_data(prop.as_dataframe)
    analyzed_prop = PropertyData.build_property_from_dataframe(analyzed_df)
    return analyzed_prop

class CompletePropertiesAnalyzer:
  """Include analysis that requires, e.g., data from both Rentcast and Rentometer."""
  def analyze_properties(self, prop_list: List[Property]) -> List[Property]:
    # TODO: Implement locale_level_analysis functions in this context to work with different non-Zillow data sources.
    raise Exception("Error: analyze_properties() called before implementation.")
    # if not isinstance(prop_list, list):
    #   raise TypeError("CompletePropertyAnalyzer takes a list of Properties. Please input the result of at least one different PropertyProvider.")
    # # TODO: make it so partial data is just skipped rather than errors out (change in add_costs functionality / move here?). Also no rentcast_url, just rentcast_id
    # # if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
    # #   raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    # prop_big_df = PropertyData.prop_list_to_dataframe(prop_list)
    # analyzed_df = add_costs_to_parsed_rentcast_data(prop_big_df)
    # analyzed_prop_list = PropertyData.build_properties_from_dataframe(analyzed_df)
    # return analyzed_prop_list
from property_data import Property, PropertyData
from typing import Protocol, List
from property_intake_clients import RentcastAPIClient, RentometerAPIClient
from property_get_options import PropertyLocationType, PropertyGetOption, JSON_GET_OPTIONS, JSON_FIRST_OPTIONS
from json_loading import json_to_df_from_disk
from property_intake_func import find_location_matches_in_cleaned_df
import pandas as pd
from pandas import DataFrame
from property_analyzers import *


class PropertyProvider(Protocol):
  def request_property(location_type: PropertyLocationType, location: str, option: PropertyGetOption) -> Property: ...

  def _clean(self, df: DataFrame) -> DataFrame: ...


class CompletePropertyProvider:
  """List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object."""
  def request_property(self, location_type: PropertyLocationType, location: str, option: PropertyGetOption) -> Property:
    all_prop_data = []

    rentcast_provider = RentcastPropertyProvider()
    rentcast_prop = rentcast_provider.request_property(location_type=location_type, location=location, option=option)
    all_prop_data.append(rentcast_prop)

    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop = rentometer_provider.request_property(location_type=location_type, location=location, option=option)
    all_prop_data.append(rentometer_prop)

    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)
    # NOTE: combine_partial_prop_data() still returns List[Property].
    if len(combined_prop_list) > 1:
      raise Exception("Error: combined_prop_list contains more than 1 element. Multiple addresses were likely detected.")
    combined_prop = combined_prop_list[0]

    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop = combined_prop_analyzer.analyze_property(combined_prop)

    return analyzed_prop


class RentcastPropertyProvider:
  """This follows the PropertyProvider Protocol and def request() outputs a partial property object."""
  def __init__(self):
    self.max_value = 550000
    self.min_bedrooms = 3
    self.min_bathrooms = 1.5
    self.property_type = "Single Family"

  def request_property(self, location_type: str, location: str, option: PropertyGetOption) -> Property:
    rentcast_df = DataFrame()

    if option in JSON_GET_OPTIONS:
      rentcast_df = json_to_df_from_disk("rentcast", "")
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(cleaned_df=rentcast_df, location_type=location_type, location=location)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentcast_df.empty): # Encompass 1) fall-through for JSON-first or 2) API call only.
      rentcast_df = RentcastAPIClient().fetch(location_type=location_type, location=location, option=option)
      rentcast_df = self._clean(rentcast_df)
      rentcast_df = find_location_matches_in_cleaned_df(cleaned_df=rentcast_df, location_type=location_type, location=location)

    if rentcast_df.empty:
      print("Warning: No properties associated with that location could be found in the Rentcast data.")

    prop = PropertyData.build_property_from_dataframe(rentcast_df)
    return prop
  
  def _clean(self, df: DataFrame) -> DataFrame:
    # df = parse_rentcast_data(df)
    max_value, min_bedrooms, min_bathrooms, property_type = self.max_value, self.min_bedrooms, self.min_bathrooms, self.property_type

    # Extract most recent home value from nested dictionary.
    value_df = pd.json_normalize(df["taxAssessments"])
    df["value"] = value_df["2025.value"]

    # Extract most recent property tax assessment.
    tax_df = pd.json_normalize(df["propertyTaxes"])
    df["property_tax"] = tax_df["2025.total"]

    # Extract relevant features.
    features_df = pd.json_normalize(df["features"])
    df["garage"] = features_df["garage"]
    df["heatingType"] = features_df["heatingType"]

    # Drop now-unpacked columns with dicts to allow for dropping duplicates
    # NOTE: Currently not storing information on owner, sale history, or HOA. Can change this / refactor Property to contain if needed
    cols_to_drop = []
    cols_to_check_to_drop = ["taxAssessments", "propertyTaxes", "features", "owner", "history", "hoa"]
    for col in cols_to_check_to_drop:
        if col in df.columns:
            cols_to_drop.append(col)
    df = df.drop(cols_to_drop, axis=1)

    # Parse dataframe by specified constants and return.
    subset_df = df[(df["value"] <= max_value) & (df["bedrooms"] >= min_bedrooms) & (df["bathrooms"] >= min_bathrooms) & (df["propertyType"] == property_type)].reset_index(drop=True)

    subset_df = subset_df.rename(columns={
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
    
    return subset_df
    

class RentometerPropertyProvider:
  def request_property(self, location_type: PropertyLocationType, location: str, option: PropertyGetOption) -> Property:
    if option in JSON_GET_OPTIONS:
      rentometer_df = json_to_df_from_disk("rentometer", "")
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(cleaned_df=rentometer_df, location_type=location_type, location=location)

    if option not in JSON_GET_OPTIONS or (option in JSON_FIRST_OPTIONS and rentometer_df.empty):
      rentometer_df = RentometerAPIClient().fetch(location_type=location_type, location=location, option=option)
      rentometer_df = self._clean(rentometer_df)
      rentometer_df = find_location_matches_in_cleaned_df(cleaned_df=rentometer_df, location_type=location_type, location=location)

    # NOTE: Rentometer specifically may give different estimations for the same address at different times. For now, just take last row.
    if len(rentometer_df) > 1:
      rentometer_df = rentometer_df.iloc[[-1]]

    prop = PropertyData.build_property_from_dataframe(rentometer_df)
    return prop
  
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
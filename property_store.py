from property_schema import Property, PropertyData, LocationDetails, FeatureDetails, AttributeDetails, ValueDetails, Metadata
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

"""Interface for intake that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  def request(location) -> Property: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop: Property) -> Property: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object.
  def request(self, location) -> Property:
    rentcast_provider = RentcastPropertyProvider()
    # TODO: currently a df, not a Property
    rentcast_prop = rentcast_provider.request(location)
    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop = rentometer_provider.request(location)
    # df = add_rent_to_parsed_rentcast_data(rentcast_prop, rentometer_df)
    # df = add_costs_to_parsed_rentcast_data(df)
    # print(df.columns)
    # TODO: centralize data processing: do analysis, rename columns, whatever
    # prop = Property().convert_cols_to_fields(df)
    # if not prop.is_complete():
    #   raise Exception("Error: Property obj is not complete at the end of CompletePropertyProvider assembly.")
    # return prop
    print(rentcast_prop)
    print(rentometer_prop)
    all_prop_data = [rentcast_prop, rentometer_prop]
    combined_prop = PropertyData.combine_prop_data(all_prop_data)
    combined_prop_analyzer = CompletePropertyAnalyzer()
    analyzed_prop = combined_prop_analyzer.analyze(combined_prop)
    return analyzed_prop


class RentcastPropertyProvider:
  # This follows the PropertyProvider Protocol and def request() outputs a partial property object. Put in CompletePropertyProvider
  # TODO: CURRENTLY RETURNS DF, NOT PARTIAL PROPERTY. So first, do work needed with DF for a given API call, add to Property, and AT THE END, analysis.
  def request(self, location) -> Property:
    # TODO: check IF the information is available saved, and if not call the API for real, instead of calling the function but actually intake "from_json_dump"
    rentcast_df = rentcast_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentcast data specifically
    # NOTE: OK, so I'm matching column names with dataclass field names, right? add this functionality to property_schema and then give DF to Property?
    rentcast_subset_df = parse_rentcast_data(rentcast_df)
    # TODO: depreciate this part of the second analysis function
    rentcast_subset_df = rentcast_subset_df.rename(columns={"formattedAddress": "street_address", "value": "value_est"})
    # TODO: actually get this from the Rentcast API finally
    rentcast_subset_df["rentcast_url"] = "placeholder"
    rentcast_prop = Property().convert_cols_to_fields(rentcast_subset_df)
    return rentcast_prop

class RentometerPropertyProvider:
  # TODO: CURRENTLY RETURNS DF, NOT PARTIAL PROPERTY. 
  def request(self, location) -> Property:
    rentometer_df = rentometer_api(location, output="from_json_dump")
    # New functionality to build a partial property from Rentometer data specifically
    rentometer_df = rentometer_df[["address", "mean", "median", "min", "max", "quickview_url"]].reset_index(drop=True)
    rentometer_df = rentometer_df.rename(columns={"quickview_url": "rentometer_url"})
    rentometer_df = rentometer_df.drop_duplicates()

    rentometer_df = rentometer_df.rename(columns={
      "mean": "mean_rent_est",
      "median": "median_rent_est",
      "min": "min_rent",
      "max": "max_rent"})

    rentometer_prop = Property().convert_cols_to_fields(rentometer_df)
    return rentometer_prop

class CompletePropertyAnalyzer:
  """Include analysis that requires, e.g., data from both Rentcast and Rentometer."""
  def analyze(self, prop: Property) -> Property:
    if not isinstance(prop, Property):
      raise TypeError("CompletePropertyAnalyzer takes a Property. Please input the result of at least one different PropertyProvider.")
    if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
      raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    # NOTE: check for Rentcast/Rentometer columns and then turn the hybrid analysis function
    # TODO: as_dataframe() @property to pass Property object into add_costs_to_parsed_rentcast_data()
    property_as_dataframe = prop.as_dataframe
    analyzed_df = add_costs_to_parsed_rentcast_data(property_as_dataframe)
    analyzed_prop = Property().convert_cols_to_fields(analyzed_df)
    return analyzed_prop

if __name__ == "__main__":
  # Test address: '5214 S Thompson Ave, Tacoma, WA 98408'
  prop_store = PropertyStore()
  prop = prop_store.get("6478 S M St, Tacoma, WA 98408")
  print(prop)
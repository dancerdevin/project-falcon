from property_schema import Property, PropertyData, LocationDetails, FeatureDetails, AttributeDetails, ValueDetails, Metadata
from typing import Protocol, List
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
  def request(location) -> List[Property]: ...

"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop: Property) -> Property: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. This will return a completely initialized Property object.
  def request(self, location) -> Property:
    rentcast_provider = RentcastPropertyProvider()

    rentcast_prop_list = rentcast_provider.request(location)
    rentometer_provider = RentometerPropertyProvider()
    rentometer_prop_list = rentometer_provider.request(location)
    all_prop_data = rentcast_prop_list + rentometer_prop_list
    combined_prop_list = PropertyData.combine_partial_prop_data(all_prop_data)
    # TODO: also update analyzer to handle a list of properties
    # combined_prop_analyzer = CompletePropertyAnalyzer()
    # analyzed_prop = combined_prop_analyzer.analyze(combined_prop)
    return combined_prop_list


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
    # TODO: this is where I should call a static method on a dataframe to return a list of properties and then take the first index and return to maintain pipeline
    # NOTE: do this for both Rentcast and Rentometer and then create func to take multiple List[Property] and combine into List[Tuple[Property]] (match on address?)
    # rentcast_prop = Property().convert_cols_to_fields(rentcast_subset_df)
    prop_list = PropertyData.build_properties_from_dataframe(rentcast_subset_df)
    # rentcast_prop = prop_list[0]
    return prop_list

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

    prop_list = PropertyData.build_properties_from_dataframe(rentometer_df)
    # rentometer_prop = prop_list[0]
    return prop_list

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
    analyzed_prop_list = PropertyData.build_properties_from_dataframe(analyzed_df)
    analyzed_prop = analyzed_prop_list[0]
    return analyzed_prop

if __name__ == "__main__":
  # Test address: '5214 S Thompson Ave, Tacoma, WA 98408'
  prop_store = PropertyStore()
  prop_list = prop_store.get("6478 S M St, Tacoma, WA 98408")
  print(prop_list[0])
  # print(prop_list[1])
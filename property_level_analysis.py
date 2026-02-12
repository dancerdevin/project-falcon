import pandas as pd
from numpy import float64
from enum import StrEnum
from json_loading import json_to_df_from_disk, json_to_list_of_dicts
from property_data_intake import rentometer_api
from datetime import datetime
from amortization.amount import calculate_amortization_amount
from property_schema import Property, LocationDetails, FeatureDetails, AttributeDetails, ValueDetails, Metadata
from typing import Dict

# TODO: currently: unpack list of property objects into dict to send to gsheet output
# then/or create Spreadsheet object to store formatting information and also plug THAT in
# TODO: generally, use Property objects instead of address_dict, once those are defined in property_data, and build plug-in for Gsheets

LOAN_TO_VALUE = .7
APR = 0.07
AMORT_MONTHS = 360
EST_YEARLY_INSURANCE = 1000

class ExpectedColumns(StrEnum):
    PROPERTY_TAX = "property_tax"


# def build_properties(rentcast_data, rentometer_data) -> list:
#     """Assemble list of Property objects populated by LocationDetails, FeatureDetails, AttributeDetails, ValueDetails, and Metadata objects."""
#     df = parse_rentcast_data(rentcast_data)
#     print(f"Stage 1: {df.head()}")

#     # Aggregate Rentometer data into Rentcast data.
#     df_with_rent = add_rent_to_parsed_rentcast_data(df, rentometer_data)
#     print(f"Stage 2: {df_with_rent.head()}")

#     # While data remains in Pandas DataFrame/Series form, perform calculations by column.
#     df_with_rent_and_costs = add_costs_to_parsed_rentcast_data(df_with_rent)
#     print(f"Stage 3: {df_with_rent_and_costs.head()}")

#     # Then, use itertuples() to efficiently treat each row as a property by turning them into NamedTuples.
#     prop_list = []

#     for row in df_with_rent_and_costs.itertuples(index=False):
#         location_details = build_location(row)
#         feature_details = build_features(row)
#         attribute_details = build_attributes(row)
#         value_details = build_values(row)
#         metadata = build_metadata(row)
#         prop_list.append(Property(location_details, feature_details, attribute_details, value_details, metadata))

#     print(f"Prop_list: {prop_list}")

#     return prop_list


# def build_location(row) -> LocationDetails:
#     # NOTE: Right now, each of these values is a Pandas Series.
#     # What I should likely do is: build_properties(), build_locations(), etc., and at each stage,
#     # return the data for each given property as a group of LocationDetails containing each Series element by index.
#     return LocationDetails(
#         street_address = row.address,
#         city = row.city,
#         state = row.state,
#         zip_code = row.zipCode,
#         county = row.county,
#         latitude = row.latitude,
#         longitude = row.longitude
#     )


# def build_features(row) -> FeatureDetails:
#     return FeatureDetails(
#         property_type = row.propertyType,
#         bedrooms = row.bedrooms,
#         bathrooms = row.bathrooms,
#         sqft = row.squareFootage,
#         lot_size = row.lotSize
#     )


# def build_attributes(row) -> AttributeDetails:
#     return AttributeDetails(
#         year_built = row.yearBuilt,
#         assessor_ID = row.assessorID,
#         legal_description = row.legalDescription,
#         owner_occupied = row.ownerOccupied
#     )


# def build_values(row) -> ValueDetails:
#     return ValueDetails(
#         value_est = row.value_est, # Note that this used to be "value," if that raises any unexpected errors
#         property_tax = row.property_tax,
#         mean_rent_est = row.mean,
#         median_rent_est = row.median,
#         min_rent = row.min,
#         max_rent = row.max,
#         mortgage_est = row.mortgage_est,
#         insurance_est = row.insurance_est,
#         monthly_tax_est = row.monthly_tax_est,
#         capex_est = row.capex_est,
#         mgmt_est = row.mgmt_est,
#         sum_est_costs = row.sum_est_costs
#     )


# def build_metadata(row) -> Metadata:
#     return Metadata(
#         filename = row.filename,
#         rentometer_url = row.rentometer_url,
#         rentcast_url = None # TODO: get from API
#     )


def parse_rentcast_data(df):
    max_value = 550000
    min_bedrooms = 3
    min_bathrooms = 1.5
    property_type = "Single Family"

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
    df = df.drop(["taxAssessments", "propertyTaxes", "features", "owner", "history", "hoa"], axis=1)
    # TODO: convert other "objects" into Pandas datatypes for ease of analysis? here or at analysis stage?

    # Ignore "filename" as this will be differ on duplicate data taken from different JSON dumps. Just keep first
    cols_to_check = [col for col in df.columns if col != 'filename']
    df = df.drop_duplicates(subset=cols_to_check)

    # Parse dataframe by specified constants and return.
    subset_df = df[(df["value"] <= max_value) & (df["bedrooms"] >= min_bedrooms) & (df["bathrooms"] >= min_bathrooms) & (df["propertyType"] == property_type)].reset_index(drop=True)
    return subset_df


def add_rent_to_parsed_rentcast_data(rentcast_data, rentometer_data):
    # For each address in parsed rentcast data, find rent data, add as expected income, and return dataframe.
    if ExpectedColumns.PROPERTY_TAX not in rentcast_data.columns.to_list():
        raise Exception("Error: property tax column missing. First call rentcast_data_parser on dataframe input.")
    
    # If I've specified a datetime, the JSON dumps already exist on disk. If not, make necessary API calls.
    # For each address in the parsed_data, apply rentometer_api function in property_data.
    # if datetime_string is None:
    #     datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     parsed_data["formattedAddress"].apply(rentometer_api)

    # Load JSON dumps saved to disk from relevant datetime (right before making API calls) and concatenate into dataframe.
    # rent_data = json_to_df("rentometer", datetime_string)
    subset_rent_data = rentometer_data[["address", "mean", "median", "min", "max", "quickview_url"]].reset_index(drop=True)
    subset_rent_data = subset_rent_data.rename(columns={"quickview_url": "rentometer_url"})
    subset_rent_data = subset_rent_data.drop_duplicates()

    # Convert relevant columns to matching floats
    cols_to_convert = ["median", "min", "max"]
    subset_rent_data[cols_to_convert] = subset_rent_data[cols_to_convert].astype(float64)

    # Match addresses between parsed_data and new Rentometer JSON dumps, add Rentometer data, and return.
    rentcast_data = rentcast_data.rename(columns={"formattedAddress": "address"})
    rentcast_data["address"] = rentcast_data["address"].astype(str)
    subset_rent_data["address"] = subset_rent_data["address"].astype(str)
    
    # Debug: check for matching addresses
    # TODO: normalize addresses during data intake?
    rentcast_addresses = set(rentcast_data["address"].unique())
    rentometer_addresses = set(subset_rent_data["address"].unique())
    print(f"Rentcast addresses: {rentcast_addresses}")
    print(f"Rentometer addresses: {rentometer_addresses}")
    print(f"Common addresses: {rentcast_addresses & rentometer_addresses}")
    
    joined_data = pd.merge(rentcast_data, subset_rent_data, on="address", how="inner") # Presumes exact same address string
    return joined_data


def add_costs_to_parsed_rentcast_data(df):
    # TODO: conform "objects" to standardized datatypes (do it here for now and figure out where to really do it later)
    # print(df.info(verbose=True))

    data_type_dict = { # Defaulting to floats for now even if ints might suffice for some
        "mean_rent_est": float64,
        "median_rent_est": float64,
        "min_rent": float64,
        "max_rent": float64,
        "mortgage_est": float64,
        "insurance_est": float64,
        "monthly_tax_est": float64,
        "capex_est": float64,
        "mgmt_est": float64,
        "sum_est_costs": float64
    }

    df = df.astype(data_type_dict)

    df["mortgage_est"] = df["value_est"].apply(lambda x: calculate_amortization_amount((x * LOAN_TO_VALUE), APR, AMORT_MONTHS))
    
    df["insurance_est"] = pd.Series(EST_YEARLY_INSURANCE / 12, index=df.index)

    df["monthly_tax_est"] = df["property_tax"] / 12 # Rentcast data is by year

    # Estimated maintenance/capex: 1% of house value per year, divided by 12 for monthly
    df["capex_est"] = df["value_est"].apply(lambda x: (x * 0.01) / 12)

    # Estimated management costs: 10% of monthly rent (using median as more robust indicator)
    df["mgmt_est"] = df["median_rent_est"] * .1

    # Estimated monthly costs, summed
    df["sum_est_costs"] = df[["mortgage_est", "insurance_est", "capex_est", "mgmt_est"]].sum(axis=1)

    return df


def clean_aggregated_property_data(list_of_dicts, index_key_match):
    """Remove fields unnecessary for or incompatible with (i.e., dictionaries) populating Google Sheet."""
    address_match_dict = {}
    columns_to_remove = ["id", "address", "addressLine2", "stateFips", "countyFips", "features", "taxAssessments", "propertyTaxes", "history", "owner"]
    for column_name, value_dicts in list_of_dicts.items():
            for key, value in value_dicts.items():
                if key == index_key_match:
                    if column_name not in columns_to_remove:
                        address_match_dict[column_name] = value

    return address_match_dict


def aggregated_property_data_calc(agg_data):
    agg_data["cost_per_sf_house"] = agg_data["value"] / agg_data["squareFootage"]
    agg_data["cost_per_sf_land"] = agg_data["value"] / agg_data["lotSize"]


def property_analysis_to_json(agg_data):
    name_string = "property_aggregate_analysis"
    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_name = f"{name_string}_{datetime_string}.json"
    agg_data.to_json(output_name, orient="columns", indent=4)


def find_address_in_property_analysis_json(address_string, datetime_string=None):
    df = json_to_df_from_disk("property_aggregate_analysis", datetime_string)
    subset_df = df[df["address"].str.contains(address_string, case=False, na=False)]
    return subset_df


def address_data_to_gsheet(address_string, datetime_string=None):
    list_of_dicts = json_to_list_of_dicts("property_aggregate_analysis", datetime_string)
    dict_index_match = None
    for i in range(len(list_of_dicts)):
        # Check all the aggregate analyses in the list of JSON dumps.
        for key, indices in list_of_dicts[i].items():
            if key == "address":
                # Focus on the address field in each dict in the list.
                for index_key, value in indices.items():
                    if address_string in value:
                        # Match found in a dict. Now hone in on the specific address data row with the index_key.
                        print("Address match found.")
                        dict_index_match = i
                        index_key_match = index_key
                        break
    
    if dict_index_match is not None:
        # Having found an address match, clean and get all information pertaining to that address.
        address_match_dict = clean_aggregated_property_data(list_of_dicts[dict_index_match], index_key_match)
    
    if address_match_dict:
        return address_match_dict
    else:
        raise Exception("Error: no match found for address string in specified JSON files.")



# property_df = rentcast_data_parser("2025-10-10_12-42-27")
# joined_data = add_rent_to_parsed_rentcast_data(property_df, "2025-10-22_13-42")
# costs_data = add_costs_to_parsed_rentcast_data(joined_data)
# df = property_aggregate_analysis("2025-10-10_12-42-27", "2025-10-22_13-42")
# property_analysis_to_json(df)
# subset_df = find_address_in_property_analysis_json("7236 S Bell St", "2025-10-28")
# subset_df.to_csv("test_find_address.csv")
# address_match = address_data_to_gsheet("7236 S Bell St", "2025-10-28")
# print(address_match)
# df = parse_rentcast_data("2025-10-10_12-42-27")
# df_with_rent = add_rent_to_parsed_rentcast_data(df, "2025-10-22_13-42")
# prop_list = build_properties("2025-10-10_12-42-27", "2025-10-22_13-42")
# print(prop_list[1])
# print(prop_list[1].values)
# print(prop_list[1].COL_NAMES)
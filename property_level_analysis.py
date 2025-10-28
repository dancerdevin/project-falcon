import pandas as pd
from enum import StrEnum
from json_to_df import json_to_df
from property_data import rentometer_api
from datetime import datetime
from amortization.amount import calculate_amortization_amount

class ExpectedColumns(StrEnum):
    PROPERTY_TAX = "property_tax"


def property_aggregate_analysis(rentcast_datetime_string=None, rentometer_datetime_string=None):
    # Parses Rentcast data in JSON dumps by datetime and incorporates Rentometer rent data and costs.
    df = rentcast_data_parser(rentcast_datetime_string)

    df_with_rent = add_rent_to_parsed_rentcast_data(df, rentometer_datetime_string)

    df_with_rent_and_cost = add_costs_to_parsed_rentcast_data(df_with_rent)

    return df_with_rent_and_cost


def rentcast_data_parser(datetime=None):
    # Use json_to_df to parse rentcast data for initial desired inputs. Returns dict subset.
    df = json_to_df("rentcast", datetime)
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

    # Parse dataframe by specified constants and return.
    subset_df = df[(df["value"] <= max_value) & (df["bedrooms"] >= min_bedrooms) & (df["bathrooms"] >= min_bathrooms) & (df["propertyType"] == property_type)].reset_index(drop=True)
    return subset_df


def add_rent_to_parsed_rentcast_data(parsed_data, datetime_string=None):
    # For each address in parsed rentcast data, find rent data, add as expected income, and return dataframe.
    if ExpectedColumns.PROPERTY_TAX not in parsed_data.columns.to_list():
        raise Exception("Error: property tax column missing. First call rentcast_data_parser on dataframe input.")
    
    # If I've specified a datetime, the JSON dumps already exist on disk. If not, make necessary API calls.
    # For each address in the parsed_data, apply rentometer_api function in property_data.
    if datetime_string is None:
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        parsed_data["formattedAddress"].apply(rentometer_api)

    # Load JSON dumps saved to disk from relevant datetime (right before making API calls) and concatenate into dataframe.
    rent_data = json_to_df("rentometer", datetime_string)
    subset_rent_data = rent_data[["address", "mean", "median", "min", "max"]].reset_index(drop=True)
    subset_rent_data = subset_rent_data.drop_duplicates()

    # Match addresses between parsed_data and new Rentometer JSON dumps, add Rentometer data, and return.
    parsed_data = parsed_data.rename(columns={"formattedAddress": "address"})
    joined_data = pd.merge(parsed_data, subset_rent_data, on="address", how="inner") # Presumes exact same address string
    return joined_data


def add_costs_to_parsed_rentcast_data(parsed_data):
    # Estimate costs: mortgage, insurance, taxes, maintenance/capex, property management, vacancy.
    loan_to_value = .7
    apr = 0.07
    amort_months = 360
    parsed_data["mortgage"] = parsed_data["value"].apply(lambda x: calculate_amortization_amount((x * loan_to_value), apr, amort_months))
    
    est_monthly_insurance = 1000 / 12
    parsed_data["insurance"] = est_monthly_insurance

    # Rentcast's property tax data is by year, so calculating month-by-month in order to sum costs.
    parsed_data["monthly_tax"] = parsed_data["property_tax"] / 12

    # Estimated maintenance/capex: 1% of house value per year, divided by 12 for monthly
    parsed_data["capex"] = parsed_data["value"].apply(lambda x: (x * 0.01) / 12)

    # Estimated management costs: 10% of monthly rent (using median as more robust indicator)
    parsed_data["management"] = parsed_data["median"] * .1

    parsed_data["sum_costs"] = parsed_data[["mortgage", "insurance", "capex", "management", "monthly_tax"]].sum(axis=1)

    return parsed_data


def property_analysis_to_json(aggregate_data):
    name_string = "property_aggregate_analysis"
    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_name = f"{name_string}_{datetime_string}.json"
    aggregate_data.to_json(output_name, orient="columns", indent=4)


def find_address_in_property_analysis_json(address_string, datetime_string=None):
    df = json_to_df("property_aggregate_analysis", datetime_string)
    subset_df = df[df["address"].str.contains(address_string, case=False, na=False)]
    return subset_df


# property_df = rentcast_data_parser("2025-10-10_12-42-27")
# joined_data = add_rent_to_parsed_rentcast_data(property_df, "2025-10-22_13-42")
# costs_data = add_costs_to_parsed_rentcast_data(joined_data)
# df = property_aggregate_analysis("2025-10-10_12-42-27", "2025-10-22_13-42")
# property_analysis_to_json(df)
# subset_df = find_address_in_property_analysis_json("7236 S Bell St", "2025-10-28")
# subset_df.to_csv("test_find_address.csv")
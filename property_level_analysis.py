from json_loading import json_to_df_from_disk
from datetime import datetime


# TODO: Evaluate respective roles of property_level_analysis.py and classes in property_store.py. What functionality should go where and why?

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
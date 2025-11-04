import pandas as pd
import glob
import os
import json
from enum import StrEnum

class ExpectedAPIs(StrEnum):
    RENTCAST = "rentcast"
    RENTOMETER = "rentometer"
    PROPERTY_AGG_ANALYSIS = "property_aggregate_analysis"


def json_to_df(api=None, datetime=None):
    files = assemble_json_file_string(api, datetime)

    df_list = []
    for file in files:
        with open(file, "r", encoding="utf-8-sig") as json_dump:
            print(f"Concatenating to dataframe: {file}")
            df = pd.read_json(json_dump)
            df["filename"] = os.path.basename(file)
            df_list.append(df)

    if not files:
        raise Exception("Error: no files found. Check API string and datetime format (year-month-day_hour-minute-second).")
    
    complete_df = pd.concat(df_list, ignore_index=True)
    return complete_df


def json_to_list_of_dicts(api=None, datetime=None):
    files = assemble_json_file_string(api, datetime)

    dict_list = []
    for file in files:
        with open(file, "r", encoding="utf-8-sig") as json_dump:
            print(f"Adding to list: {file}")
            dict = json.load(json_dump)
            dict_list.append(dict)

    if not files:
        raise Exception("Error: no files found. Check API string and datetime format (year-month-day_hour-minute-second).")
    
    return dict_list


def assemble_json_file_string(api, datetime):
    if api and api not in [ExpectedAPIs.RENTCAST, ExpectedAPIs.RENTOMETER, ExpectedAPIs.PROPERTY_AGG_ANALYSIS]:
        raise Exception("Error: acceptable name strings are 'rentcast', 'rentometer', and 'property_aggregate_analysis'.")

    if not api and not datetime:
        files = glob.glob("*.json")

    else:
        glob_string = "*"
        if api:
            glob_string += f"{api.lower()}_"
        if datetime:
            glob_string += f"{datetime}"
        glob_string += "*.json"
        files = glob.glob(glob_string)

    return files

# df = json_to_df("rentcast", "2025-10-10_12-42")
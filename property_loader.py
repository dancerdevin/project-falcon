import pandas as pd
import glob
import os
import json
from enum import StrEnum

class PropertySources(StrEnum):
    RENTCAST = "rentcast"
    RENTOMETER = "rentometer"
    PROPERTY_AGG_ANALYSIS = "property_aggregate_analysis"

class JSONPropertyLoader:
    @staticmethod
    def load_as_df(source, datetime):
        files = JSONPropertyLoader._assemble_json_file_string(source, datetime)

        df_list = []
        for file in files:
            with open(file, "r", encoding="utf-8-sig") as json_dump:
                print(f"Concatenating to dataframe: {file}")
                df = pd.read_json(json_dump)
                if source == PropertySources.RENTCAST or source == PropertySources.RENTOMETER:
                    df[f"{source}_filename"] = os.path.basename(file)
                df_list.append(df)

        if not files:
            raise Exception("Error: no files found. Check API string and datetime format (year-month-day_hour-minute-second).")

        complete_df = pd.concat(df_list, ignore_index=True)
        return complete_df

    @staticmethod
    def load_as_list_of_dicts(source, datetime):
        files = JSONPropertyLoader._assemble_json_file_string(source, datetime)

        dict_list = []
        for file in files:
            with open(file, "r", encoding="utf-8-sig") as json_dump:
                print(f"Adding to list: {file}")
                dict = json.load(json_dump)
                dict_list.append(dict)

        if not files:
            raise Exception("Error: no files found. Check API string and datetime format (year-month-day_hour-minute-second).")
        
        return dict_list

    @staticmethod
    def _assemble_json_file_string(source, datetime):
        if source and source not in [PropertySources.RENTCAST, PropertySources.RENTOMETER, PropertySources.PROPERTY_AGG_ANALYSIS]:
            raise Exception("Error: acceptable name strings are 'rentcast', 'rentometer', and 'property_aggregate_analysis'.")

        if not source and not datetime:
            files = glob.glob("*.json")

        else:
            glob_string = "*"
            if source:
                glob_string += f"{source.lower()}_"
            if datetime:
                glob_string += f"{datetime}"
            glob_string += "*.json"
            files = glob.glob(glob_string)

        return files
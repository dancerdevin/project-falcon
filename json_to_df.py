import pandas as pd
import glob
import os


def json_to_df(api=None, datetime=None):
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

    df_list = []
    for file in files:
        with open(file, 'r') as json_dump:
            print(f"Concatenating to dataframe: {file}")
            df = pd.read_json(json_dump)
            df["filename"] = os.path.basename(file)
            df_list.append(df)

    if not files:
        raise Exception("Error: no files found. Check API string and datetime format (year-month-day_hour-minute-second).")
    
    complete_df = pd.concat(df_list, ignore_index=True)
    return complete_df


# df = json_to_df("rentcast", "2025-10-10_12-42")
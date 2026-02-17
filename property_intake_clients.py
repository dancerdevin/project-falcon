from property_intake_func import location_params, api_call_for_json
import os
from property_get_options import UPDATE_JSON_OPTIONS
import math
import pandas as pd
from io import StringIO


# TODO: standardize format of fetch() between intake API clients however possible
class RentcastAPIClient:
   def fetch(self, location, option, results=500):
    print("Calling Rentcast API function for " + str(location))
    # Write JSON dump from Rentcast API call.
    API_KEY = os.getenv("RENTCAST_API_KEY")
    URL = "https://api.rentcast.io/v1/properties"
    data = None

    default_params = {
        "api_key": API_KEY,
        "bedrooms": "3",
        "baths": "1.5+",
        "price": "250000:550000",
    }

    params = location_params(location, default_params)

    headers = {
        "X-API-KEY": API_KEY,
    }

    if not isinstance(results, int):
        raise Exception("Error: please input a valid integer for the number of results requested.")
    elif results > 500:
        print("Offset required, as result exceeds limit of 500. Attempting multiple calls.")
        self._multiple_rentcast_calls_with_offset(URL, params, headers, results, option)
    else:
        params["limit"] = results
        if not option:
            raise Exception("Error: please specify PropertyGetOption")

        else:
            save_to_disk = True if option in UPDATE_JSON_OPTIONS else False
            data = api_call_for_json(URL, params, "rentcast", headers=headers, save_to_disk=save_to_disk)

    return data
   
   def _multiple_rentcast_calls_with_offset(URL, params, headers, results, option):
    number_of_calls = math.ceil(results / 500)
    # TODO: incorporate redundant code into json_loading functionality
    df_list = []
    for i in range(1, number_of_calls):
        params["offset"] = str(i * 500)
        print("Attempting API call with offset of " + params["offset"])
        save_to_disk = True if option in UPDATE_JSON_OPTIONS else False
        data = api_call_for_json(URL, params, "rentcast", headers, save_to_disk)
        with open(data, "r", encoding="utf-8-sig") as json_dump:
            print(f"Concatenating data subset {i} to dataframe")
            df = pd.read_json(StringIO(json_dump))
    df_list.append(df)
    complete_df = pd.concat(df_list, ignore_index=True)
    return complete_df


class RentometerAPIClient:
  def fetch(self, location, option):
    # Write JSON dump from Rentometer API call.
    print("Calling Rentometer API function for " + str(location))
    API_KEY = os.getenv("RENTOMETER_API_KEY")
    URL = "https://www.rentometer.com/api/v1/summary"
    data = None

    default_params = {
        "api_key": API_KEY,
        "bedrooms": "3",
        "baths": "1.5+",
        "building_type": "house"
    }

    params = location_params(location, default_params)

    if not option:
        raise Exception("Error: please specify PropertyGetOption")
    else:
        save_to_disk = True if option in UPDATE_JSON_OPTIONS else False
        data = api_call_for_json(URL, params, "rentometer", save_to_disk=save_to_disk)
            
    return data
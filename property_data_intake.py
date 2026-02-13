import requests
import json
import pgeocode
from dotenv import load_dotenv
from datetime import datetime
from geopy.geocoders import Nominatim
import math
import pandas as pd
from json_loading import json_to_df_from_disk
from io import StringIO


load_dotenv() # Load API keys
geolocator = Nominatim(user_agent="peregrin_app") # Instantiate address-finder

# TODO: PropertyIntake protocol for RentcastPropertyIntake/RentometerPropertyIntake .get() with overrides

VALID_OUTPUTS = [
    "dump_to_disk_no_pub",      # Call API, save to disk, stop there
    "dump_to_disk_then_pub",    # Call API, save to disk, then pass on to Gsheets
    "direct_to_gsheets",        # Call API, don't save to disk, pass on to Gsheets
    "from_json_dump"            # Do not call API, pass existing JSON dump to Gsheets
]


def lat_long_from_zip(zip_code):
    # Return central latitude and longitude for a given ZIP code, for use in API calls.
    nomi = pgeocode.Nominatim('us')

    zip_code = str(zip_code) # Stringify for query
    location = nomi.query_postal_code(zip_code)

    latitude = location.latitude
    longitude = location.longitude
    print(f"Central latitude for ZIP: {latitude}")
    print(f"Central longitude for ZIP: {longitude}")

    return [str(latitude), str(longitude)] # Stringify for API call and return as list


def location_params(location, params):
    # Meta-function to determine if API call will be passed an address or a lat-long.
    if isinstance(location, str):
        if " " not in location: # Infer input without whitespace is stringified zipcode
            params["zipCode"] = location
        else: # Infer input with whitespace is address
            location = ' '.join(location.split()) # Normalize whitespace from JSON dump
            params["address"] = location

    elif isinstance(location, int):
        if len(str(location)) != 5:
            raise Exception("Error: invalid zipcode input. Must have length of 5.")
        params["zipCode"] = location

    elif isinstance(location, list):
        if len(location) != 2:
            raise Exception("Error: list input should contain two elements, latitude and longitude.")
        params["latitude"] = location[0]
        params["longitude"] = location[1]

    else:
        raise Exception("Error: for location, please input either an address as a string or lat-long as list.")
    
    return params


def closest_address_to_lat_long(latitude, longitude):
    location = geolocator.reverse(f"{latitude}, {longitude}")
    if location:
        return location.address
    else:
        raise Exception("Error: Geolocator did not return a valid location.")
    

def api_call_for_json(url, params, name_string, save_to_disk=True, headers={}):
    # Centralized meta-function for API calls. Writes .json file to disk.
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = f"{name_string}_{datetime_string}.json"

        if save_to_disk:
            with open(output_name, "w") as f:
                json.dump(data, f, indent=4)

        # Convert to DF
        json_file = StringIO(json.dumps(data))
        df = pd.read_json(json_file)
        df["filename"] = ""

        return df

    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")


def multiple_rentcast_calls_with_offset(URL, params, headers, results, output):
    number_of_calls = math.ceil(results / 500)
    # TODO: incorporate redundant code into json_loading functionality
    df_list = []
    for i in range(1, number_of_calls):
        params["offset"] = str(i * 500)
        print("Attempting API call with offset of " + params["offset"])
        save_to_disk = True if output == "dump_to_disk" else False
        data = api_call_for_json(URL, params, "rentcast", headers, save_to_disk)
        with open(data, "r", encoding="utf-8-sig") as json_dump:
            print(f"Concatenating data subset {i} to dataframe")
            df = pd.read_json(StringIO(json_dump))
    df_list.append(df)
    complete_df = pd.concat(df_list, ignore_index=True)
    return complete_df


def parse_rentcast_json_by_zip(data, zipcode):
    # Find all entries in a JSON dump with the actual ZIP code (as properties in the vicinity might be included)
    with open(data, 'r') as file:
        json_data = json.load(file)
    subset_data = [entry for entry in json_data if entry.get("zipCode") == str(zipcode)]


# lat_long = lat_long_from_zip(98408)
# address = closest_address_to_lat_long(latitude, longitude)
# rentometer_api(lat_long)
# rentcast_api(98408, 2200)
# parse_rentcast_json_by_zip("rentcast_2025-10-09_16-22-59.json", 98408)
# rentometer_api("6478 S M St, Tacoma, WA 98408")
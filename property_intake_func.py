import requests
import json
import pgeocode
from dotenv import load_dotenv
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from io import StringIO


# TODO: Evaluate respective roles of property_intake_func.py and property_intake_clients.py. What functionality should go where and why?
# TODO: Normalization of street address strings (this will surely be an issue at some point, even if Rentcast/Rentometer are consistent)

load_dotenv() # Load API keys
geolocator = Nominatim(user_agent="peregrin_app") # Instantiate address-finder


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


def location_params(location, params={}):
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

        # Convert to DF
        json_file = StringIO(json.dumps(data))
        df = pd.read_json(json_file)

        if save_to_disk:
            with open(output_name, "w") as f:
                json.dump(data, f, indent=4)
            df[f"{name_string}_filename"] = output_name

        else:
            df[f"{name_string}_filename"] = ""

        return df

    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")


def find_location_matches_in_cleaned_df(cleaned_df, location):
    """For a PropertyProvider, check if a DataFrame retrieved from JSON dumps contains target location.
    If not, return empty DF to trigger fall-through to an external API call."""
    params = location_params(location)

    # Possible keys: "address", "zipCode", "latitude", "longitude." Assume I'm asking exclusively for 1) address, 2) zip, 3) lat-long
    if "address" in params:
        subset_df = cleaned_df[cleaned_df["street_address"] == params["address"]]

    elif "zipCode" in params:
        subset_df = cleaned_df[cleaned_df["zip_code"] == params["zipCode"]]

    elif "latitude" in params and "longitude" in params:
        subset_df = cleaned_df[cleaned_df["latitude"] == params["latitude"] and cleaned_df["longitude"] == params["longitude"]]

    else:
        raise Exception("Error: location_params() returned no recognized keys in params dict.")
    
    # Drop dupes. Ignore, e.g, "rentcast_filename" as this will be differ on duplicate data taken from different JSON dumps. Just keep first
    cols_to_check = [col for col in subset_df.columns if "filename" not in col and "url" not in col]
    subset_df = subset_df.drop_duplicates(subset=cols_to_check)
    print(subset_df)

    df_length = len(subset_df)
    print(f"Number of rows in DataFrame after JSON location match check: {df_length}")

    return subset_df # If there are no matches, subset_df.empty will return True.
import requests
import json
import pgeocode
import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv() # Load API keys


def lat_long_from_zip(zip_code):
    # Return central latitude and longitude for a given ZIP code, for use in API calls.
    nomi = pgeocode.Nominatim('us')

    zip_code = str(zip_code) # Stringify for query
    location = nomi.query_postal_code(zip_code)

    latitude = location.latitude
    longitude = location.longitude
    print(f"Central latitude for ZIP: {latitude}")
    print(f"Central longitude for ZIP: {longitude}")

    return str(latitude), str(longitude) # Stringify for API call


def rentometer_api(latitude, longitude):
    # Write JSON dump from Rentometer API call.
    API_KEY = os.getenv("RENTOMETER_API_KEY")
    URL = "https://www.rentometer.com/api/v1/summary"

    params = {
        "api_key": API_KEY,
        "latitude": latitude,
        "longitude": longitude,
        "bedrooms": "3",
        "baths": "1.5+",
        "building_type": "house"
    }

    try:
        response = requests.get(URL, params=params)
        response.raise_for_status()

        data = response.json()
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = f"rentometer_{datetime_string}.json"

        with open(output_name, "w") as f:
            json.dump(data, f, indent=4)

    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")


def rentcast_api(latitude, longitude):
    # Write JSON dump from Rentcast API call.
    API_KEY = os.getenv("RENTCAST_API_KEY")
    URL = "https://api.rentcast.io/v1/properties"

    params = {
        "api_key": API_KEY,
        "latitude": latitude,
        "longitude": longitude,
        "bedrooms": "3",
        "baths": "1.5+",
        "radius": "5",
    }

    headers = {
        "X-API-KEY": API_KEY,
    }

    try:
        response = requests.get(URL, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_name = f"rentcast_{datetime_string}.json"

        with open(output_name, "w") as f:
            json.dump(data, f, indent=4)

    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")


def parse_rentcast_json_by_zip(data, zipcode):
    # Find all entries in a JSON dump with the actual ZIP code (as properties in the vicinity might be included)
    with open(data, 'r') as file:
        json_data = json.load(file)
    subset_data = [entry for entry in json_data if entry.get("zipCode") == str(zipcode)]
    print(subset_data)


latitude, longitude = lat_long_from_zip(98408)
# rentometer_api(latitude, longitude)
# rentcast_api(latitude, longitude)
# parse_rentcast_json_by_zip("rentcast_2025-10-06_15-40-25.json", 98408)
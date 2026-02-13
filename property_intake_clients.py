from property_data_intake import location_params, json_to_df_from_disk, api_call_for_json, multiple_rentcast_calls_with_offset
import os

# TODO: standardize format of fetch() between intake API clients however possible
class RentcastAPIClient:
   def fetch(self, location, results=500, output=""):
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
        multiple_rentcast_calls_with_offset(URL, params, headers, results, output)
    else:
        params["limit"] = results
        if not output:
            raise Exception("Error: please specify output from list of VALID_OUTPUTS.")
        elif output == "from_json_dump":
            # For testing purposes, just return a filename string to load an already saved JSON
            data = json_to_df_from_disk("rentcast", "")
        else:
            save_to_disk = False if output == "direct_to_gsheets" else True
            data = api_call_for_json(URL, params, "rentcast", headers=headers, save_to_disk=save_to_disk)

    return data


class RentometerAPIClient:
  def fetch(self, location, output=""):
    # Write JSON dump from Rentometer API call.
    print("Calling rentometer API function for " + str(location))
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

    if not output:
        raise Exception("Error: please specify output from list of VALID_OUTPUTS.")
    elif output == "from_json_dump":
        # For testing purposes, just return a filename string to load an already saved JSON
        data = json_to_df_from_disk("rentometer", "")
    else:
        save_to_disk = False if output == "direct_to_gsheets" else True
        data = api_call_for_json(URL, params, "rentometer", save_to_disk=save_to_disk)
            
    return data
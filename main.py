from property_data_intake import *
from property_level_analysis import *
from spreadsheets import *
from property_schema import *
# from gsheets.gsheets_client import GoogleSheetsAPIClient, SPREADSHEET_TITLE, SHEET_ONE_TITLE
# from gsheets.create_gsheet import GoogleSheet
# from gsheets.update_gsheet import PropertySpreadsheet, PropertyGsheet


VALID_OUTPUTS = [
    "json",
    "gsheets"
]

def zipcode_to_disk(zip: int, output):
    lat_long = lat_long_from_zip(zip)
    # address = closest_address_to_lat_long(latitude, longitude)
    rentometer_api(lat_long)
    rentcast_api(98408, 2200)
    # parse_rentcast_json_by_zip("rentcast_2025-10-09_16-22-59.json", 98408)
    # rentometer_api("6478 S M St, Tacoma, WA 98408")


if __name__ == "__main__":
   zipcode_to_disk(98408, "json")
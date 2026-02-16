from property_data_intake import *
from property_level_analysis import *
from spreadsheets import *
from property_schema import *
from gsheets.gsheets_client import GoogleSheetsAPIClient, SPREADSHEET_TITLE, SHEET_ONE_TITLE
from gsheets.create_gsheet import GoogleSheet
from gsheets.update_gsheet import PropertySpreadsheet, PropertyGsheet
from property_store import PropertyStore


def zipcode_to_output(location, output):
    # if output not in VALID_OUTPUTS:
    #     raise Exception("Error: requested output not in list of valid outputs.")
    
    # TODO: confirm in what context I need to go zip -> lat_long -> address? For Rentometer?
    # lat_long = lat_long_from_zip(zip)
    # address = closest_address_to_lat_long(latitude, longitude)
    # rentometer_result = rentometer_api(location, output)
    # rentcast_result = rentcast_api(location, 100, output)
    # parse_rentcast_json_by_zip("rentcast_2025-10-09_16-22-59.json", 98408)
    # rentometer_api("6478 S M St, Tacoma, WA 98408")

    if output != "dump_to_disk_no_pub":
        # prop_list = build_properties(rentometer_datetime_string=rentometer_result, rentcast_datetime_string=rentcast_result)
        # prop_list = build_properties(rentometer_data=rentometer_result, rentcast_data=rentcast_result)
        # prop_obj = prop_list[0]
        prop_store = PropertyStore()
        prop_list = prop_store.get("6478 S M St, Tacoma, WA 98408")
        prop_obj = prop_list[0]

        client = GoogleSheetsAPIClient()
        gsheet = GoogleSheet(client.client, SPREADSHEET_TITLE, SHEET_ONE_TITLE)
        prop_sheet = PropertySpreadsheet(prop_obj)
        property_gsheet = PropertyGsheet(prop_sheet, gsheet)
        property_gsheet.update_values()
        property_gsheet.update_format()


if __name__ == "__main__":
   # zipcode_to_output(98408, "from_json_dump")
   zipcode_to_output('5214 S Thompson Ave, Tacoma, WA 98408', "direct_to_gsheets")
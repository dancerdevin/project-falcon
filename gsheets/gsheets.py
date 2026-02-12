import os
import sys
from gsheets_client import GoogleSheetsAPIClient, SPREADSHEET_TITLE, SHEET_ONE_TITLE
from create_gsheet import GoogleSheet
from update_gsheet import PropertySpreadsheet, PropertyGsheet

# Locate parent directory to import property data scripts
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from property_level_analysis import *
from spreadsheets import *
from property_schema import *

# DATETIME_STRING used to parse JSON filenames for addresses containing ADDRESS_STRING
ADDRESS_STRING = "7236 S Bell St"
DATETIME_STRING = "2025-10-28"


def main():
  # address_dict = address_data_to_gsheet(ADDRESS_STRING, DATETIME_STRING)
  # prop_list = build_properties("2025-10-10_12-42-27", "2025-10-22_13-42")
  # prop_obj = prop_list[0]
  # layout = build_layout(prop_obj)
  # TODO: hook up PropertyStore instead

  client = GoogleSheetsAPIClient()
  gsheet = GoogleSheet(client.client, SPREADSHEET_TITLE, SHEET_ONE_TITLE)
  prop_sheet = PropertySpreadsheet(prop_obj)
  property_gsheet = PropertyGsheet(prop_sheet, gsheet)
  property_gsheet.update_values()
  property_gsheet.update_format()


if __name__ == "__main__":
  main()
import os
import sys
# from property_gsheets import repeat_cell_builder
from gsheets import GoogleSheetsAPIClient, GoogleSheet


# Locate parent directory to import property data scripts
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from property_level_analysis import address_data_to_gsheet

# DATETIME_STRING used to parse JSON filenames for addresses containing ADDRESS_STRING
ADDRESS_STRING = "7236 S Bell St"
DATETIME_STRING = "2025-10-28"

# Spreadsheet constants, e.g., title
SPREADSHEET_TITLE = "Post Refactor Empty Test"
SHEET_ONE_TITLE = "Test Sheet"


def main():
  address_dict = address_data_to_gsheet(ADDRESS_STRING, DATETIME_STRING)
  client = GoogleSheetsAPIClient()
  gsheet = GoogleSheet(client.client, SPREADSHEET_TITLE, SHEET_ONE_TITLE)


if __name__ == "__main__":
  main()
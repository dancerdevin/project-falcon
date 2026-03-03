from typing import Protocol
from spreadsheets import *
from property_data import Property
from gsheets.gsheets_client import GoogleSheetsAPIClient
from gsheets.gsheet import GoogleSheet
from gsheets.property_gsheet import PropertySpreadsheet, PropertyGsheet

# TODO: test publish_gsheets_from_property_list() and consider how/where to store. Just a free-floating function in this script right now.

# Spreadsheet publishing constants. For PropertyGsheets, Property address will be prepended to suffixes
GSHEET_SPREADSHEET_TITLE_SUFFIX = "Property Spreadsheet"
GSHEET_SHEET_ONE_TITLE_SUFFIX = "Property Sheet"

class PropertyPublisher(Protocol):
  def publish(self, prop: Property): ...

class PropertyGsheetPublisher:
  def publish(self, prop: Property):
    client = GoogleSheetsAPIClient()
    spreadsheet_title = prop.location.street_address + " " + GSHEET_SPREADSHEET_TITLE_SUFFIX
    sheet_one_title = prop.location.street_address + " " + GSHEET_SHEET_ONE_TITLE_SUFFIX
    gsheet = GoogleSheet(client.client, spreadsheet_title=spreadsheet_title, sheet_one_title=sheet_one_title)
    prop_sheet = PropertySpreadsheet(prop)
    property_gsheet = PropertyGsheet(prop_sheet, gsheet)
    property_gsheet.update_values()
    property_gsheet.update_format()

def publish_gsheets_from_property_list(prop_list: List[Property]):
  if not isinstance(prop_list, list):
    raise TypeError("Must pass a list of Properties for looping.")
  
  for prop in prop_list:
    PropertyGsheetPublisher().publish(prop)
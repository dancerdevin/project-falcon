import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from enum import StrEnum
from property_level_analysis import address_data_to_gsheet


address_string = "7236 S Bell St"
datetime_string = "2025-10-28"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class FormatKwargs(StrEnum):
  """Expected kwargs for formatting updates using repeat_cell_builder()."""
  BG_COLOR = "bg_color"
  TEXT_COLOR = "text_color"


def repeat_cell_builder(sheet_id, start_row, end_row, start_col, end_col, **kwargs):
  """Formatting requests in the Google Sheets API involve many complex nested arrays.
  This helper function unpacks specifications to fit the necessary structure."""

  repeat_cell = {
    "repeatCell": {
      "range": {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_col,
        "endColumnIndex": end_col
      },
      "cell": {"userEnteredFormat": {}},
      "fields": "userEnteredFormat"
    }
  }

  user_format_dict = repeat_cell["repeatCell"]["cell"]["userEnteredFormat"]
  fields = []

  # Check for dictionaries with kwargs
  if FormatKwargs.BG_COLOR in kwargs:
    user_format_dict["backgroundColor"] = kwargs["bg_color"]
    fields.append("backgroundColor")
  
  if FormatKwargs.TEXT_COLOR in kwargs:
    if "textFormat" not in user_format_dict:
      user_format_dict["textFormat"] = {}
    user_format_dict["textFormat"]["foregroundColor"] = kwargs["text_color"]
    fields.append("textFormat.foregroundColor")
  
  # Join fields list into required fields string
  repeat_cell["repeatCell"]["fields"] = "userEnteredFormat(" + ",".join(fields) + ")"

  return repeat_cell


def main():
  """Generate Google Sheet from aggregate data on a single property."""
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  spreadsheet_title = "BatchUpdate Test Spreadsheet with Colors SORTED V3.3"
  sheet_one_title = "Test Sheet"

  sheet_body = {
    "properties": {
      "title": spreadsheet_title
    },
    "sheets": [
      {
        "properties": {
          "title": sheet_one_title
        }
      }
    ]
  }

  try:
    service = build("sheets", "v4", credentials=creds)

    # Create spreadsheet
    spreadsheet = service.spreadsheets().create(body=sheet_body).execute()

    print(f"Spreadsheet created: {spreadsheet.get("spreadsheetUrl")}")

    spreadsheet_id = spreadsheet.get("spreadsheetId")

    address_dict = address_data_to_gsheet(address_string, datetime_string)

    # Populate spreadsheet with values using spreadsheet.values().batchUpdate()
    categories = ["Location", "", "", "Features", "", "", "Values", "", "", "Metadata"]
    location_keys = ["addressLine1", "city", "state", "zipCode", "county", "latitude", "longitude"]
    features_keys = ["propertyType", "bedrooms", "bathrooms", "squareFootage", "lotSize", "yearBuilt", "zoning", "garage", "heatingType"]
    values_keys = ["lastSalePrice", "ownerOccupied", "value", "propertyTax", "mean", "median", "min", "max", "mortgage", "insurance", "monthly_tax", "capex", "management", "sum_costs"]
    metadata_keys = ["assessorID", "legalDescription", "lastSaleDate", "filename"]
    location_dict = {key: address_dict[key] for key in location_keys if key in address_dict}
    features_dict = {key: address_dict[key] for key in features_keys if key in address_dict}
    values_dict = {key: address_dict[key] for key in values_keys if key in address_dict}
    metadata_dict = {key: address_dict[key] for key in metadata_keys if key in address_dict}

    # Dynamically map ranges and values to body data, maintaining key-value parallelism with dicts
    ranges = [
      (sheet_one_title + "!B1:1", categories, "ROWS"),
      (sheet_one_title + "!A2:A", list(location_dict.keys()), "COLUMNS"),
      (sheet_one_title + "!B2:B", list(location_dict.values()), "COLUMNS"),
      (sheet_one_title + "!D2:D", list(features_dict.keys()), "COLUMNS"),
      (sheet_one_title + "!E2:E", list(features_dict.values()), "COLUMNS"),
      (sheet_one_title + "!G2:G", list(values_dict.keys()), "COLUMNS"),
      (sheet_one_title + "!H2:H", list(values_dict.values()), "COLUMNS"),
      (sheet_one_title + "!J2:J", list(metadata_dict.keys()), "COLUMNS"),
      (sheet_one_title + "!K2:K", list(metadata_dict.values()), "COLUMNS")
    ]

    values_body = {
      "valueInputOption": "RAW",
      "data": [
        {"range": range, "values": [values], "majorDimension": majorDimension} for range, values, majorDimension in ranges
      ]
    }

    service.spreadsheets().values().batchUpdate(
      spreadsheetId = spreadsheet_id,
      body = values_body
    ).execute()
    print("spreadsheets.values.batchUpdate executed.")

    # Format spreadsheet using spreadsheet.batchUpdate(). First get sheet ID
    sheet_id = None
    
    for sheet in spreadsheet["sheets"]:
      if sheet["properties"]["title"] == sheet_one_title:
        sheet_id = sheet["properties"]["sheetId"]
    if sheet_id is None:
      raise Exception("Error: No match with sheet title found.")

    # Dynamically map ranges, formatting, and fields to format requests
    format_specs = [
      {
          "range": (0, 1, 1, 2),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 4, 5),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 7, 8),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 10, 11),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (1, len(location_keys) + 1, 0, 1),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(features_keys) + 1, 3, 4),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(values_keys) + 1, 6, 7),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(metadata_keys) + 1, 9, 10),
          FormatKwargs.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwargs.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      }
    ]

    # start_row, end_row, start_col, end_col are unpacked from "range" tuple; dicts like bg_color are unpacked as kwargs.
    format_body = {
      "requests": [
        repeat_cell_builder(sheet_id, *spec["range"], **spec) for spec in format_specs
      ]
    }

    service.spreadsheets().batchUpdate(
      spreadsheetId = spreadsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")


  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()
from gsheets import SHEET_ONE_TITLE

"""
Populate Google Sheet object with property data by updating values and formatting.
"""


class Format:
  """Expected kwargs for formatting updates using repeat_cell_builder()."""
  BG_COLOR = "bg_color"
  TEXT_COLOR = "text_color"


CATEGORY_HEADERS = ["Location", "", "", "Features", "", "", "Values", "", "", "Metadata"]
LOCATION_KEYS = ["addressLine1", "city", "state", "zipCode", "county", "latitude", "longitude"]
FEATURES_KEYS = ["propertyType", "bedrooms", "bathrooms", "squareFootage", "lotSize", "yearBuilt", "zoning", "garage", "heatingType"]
VALUES_KEYS = ["lastSalePrice", "ownerOccupied", "value", "propertyTax", "mean", "median", "min", "max", "mortgage", "insurance", "monthly_tax", "capex", "management", "sum_costs"]
METADATA_KEYS = ["assessorID", "legalDescription", "lastSaleDate", "filename"]


class PropertySpreadsheet:
  def __init__(self, address_dict, gsheet):
    self.address_dict = address_dict
    self.gsheet = gsheet
    self.gsheet_id = gsheet.spreadsheet.get("spreadsheetId")

  def update_values(self):
    """Populate spreadsheet with values using spreadsheet.values().batchUpdate()."""
    address_dict = self.address_dict
    location_dict = {key: address_dict[key] for key in LOCATION_KEYS if key in address_dict}
    features_dict = {key: address_dict[key] for key in FEATURES_KEYS if key in address_dict}
    values_dict = {key: address_dict[key] for key in VALUES_KEYS if key in address_dict}
    metadata_dict = {key: address_dict[key] for key in METADATA_KEYS if key in address_dict}

    # Dynamically map ranges and values to body data, maintaining key-value parallelism with dicts
    ranges = [
      (SHEET_ONE_TITLE + "!B1:1", CATEGORY_HEADERS, "ROWS"),
      (SHEET_ONE_TITLE + "!A2:A", list(location_dict.keys()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!B2:B", list(location_dict.values()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!D2:D", list(features_dict.keys()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!E2:E", list(features_dict.values()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!G2:G", list(values_dict.keys()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!H2:H", list(values_dict.values()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!J2:J", list(metadata_dict.keys()), "COLUMNS"),
      (SHEET_ONE_TITLE + "!K2:K", list(metadata_dict.values()), "COLUMNS")
    ]

    values_body = {
      "valueInputOption": "RAW",
      "data": [
        {"range": range, "values": [values], "majorDimension": majorDimension} for range, values, majorDimension in ranges
      ]
    }

    self.gsheet.client.spreadsheets().values().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = values_body
    ).execute()
    print("spreadsheets.values.batchUpdate executed.")

  def repeat_cell_builder(self, sheet_id, start_row, end_row, start_col, end_col, **kwargs):
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
    if Format.BG_COLOR in kwargs:
      user_format_dict["backgroundColor"] = kwargs["bg_color"]
      fields.append("backgroundColor")
    
    if Format.TEXT_COLOR in kwargs:
      if "textFormat" not in user_format_dict:
        user_format_dict["textFormat"] = {}
      user_format_dict["textFormat"]["foregroundColor"] = kwargs["text_color"]
      fields.append("textFormat.foregroundColor")
    
    # Join fields list into required fields string
    repeat_cell["repeatCell"]["fields"] = "userEnteredFormat(" + ",".join(fields) + ")"

    return repeat_cell
  
  def update_format(self):
    """# Format spreadsheet using spreadsheet.batchUpdate(). First get sheet ID"""
    sheet_id = None
    
    for sheet in self.gsheet.spreadsheet["sheets"]:
      if sheet["properties"]["title"] == SHEET_ONE_TITLE:
        sheet_id = sheet["properties"]["sheetId"]
    if sheet_id is None:
      raise Exception("Error: No match with sheet title found.")

    # Dynamically map ranges, formatting, and fields to format requests
    format_specs = [
      {
          "range": (0, 1, 1, 2),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 4, 5),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 7, 8),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (0, 1, 10, 11),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1},
      },
      {
          "range": (1, len(LOCATION_KEYS) + 1, 0, 1),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(FEATURES_KEYS) + 1, 3, 4),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(VALUES_KEYS) + 1, 6, 7),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      },
      {
          "range": (1, len(METADATA_KEYS) + 1, 9, 10),
          Format.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          Format.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
      }
    ]

    # start_row, end_row, start_col, end_col are unpacked from "range" tuple; dicts like bg_color are unpacked as kwargs.
    format_body = {
      "requests": [
        self.repeat_cell_builder(sheet_id, *spec["range"], **spec) for spec in format_specs
      ]
    }

    self.gsheet.client.spreadsheets().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")
  
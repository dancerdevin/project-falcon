from gsheets import SHEET_ONE_TITLE

"""
Populate Google Sheet object with property data by updating values and formatting.
"""


class FormatKwarg:
  """Expected kwargs for formatting updates using repeat_cell_builder()."""
  BG_COLOR = "bg_color"
  TEXT_COLOR = "text_color"

class ValueData:
  """Data required to update values includes cell range as A1 format string, values, and major_dimension (rows or columns)."""
  def __init__(self, range, values, major_dimension):
    self.range = range
    self.values = values
    self.major_dimension = major_dimension

class GridRange:
  """Ranges to update formatting, in int format."""
  def __init__(self, start_row, end_row, start_col, end_col):
    self.start_row = start_row
    self.end_row = end_row
    self.start_col = start_col
    self.end_col = end_col

class FormatSpec:
  """Data required to update format includes cell range in a tuple of ints and FormatKwargs."""
  def __init__(self, grid_range, **kwargs):
    self.grid_range = grid_range
    self.kwargs = kwargs


CATEGORY_HEADERS = ["Location", "", "", "Features", "", "", "Values", "", "", "Metadata"]
LOCATION_KEYS = ["addressLine1", "city", "state", "zipCode", "county", "latitude", "longitude"]
FEATURES_KEYS = ["propertyType", "bedrooms", "bathrooms", "squareFootage", "lotSize", "yearBuilt", "zoning", "garage", "heatingType"]
VALUES_KEYS = ["lastSalePrice", "ownerOccupied", "value", "propertyTax", "mean", "median", "min", "max", "mortgage", "insurance", "monthly_tax", "capex", "management", "sum_costs"]
METADATA_KEYS = ["assessorID", "legalDescription", "lastSaleDate", "filename"]


class PropertySpreadsheet:
  def __init__(self, address_dict, gsheet):
    self.gsheet = gsheet
    self.gsheet_id = gsheet.spreadsheet.get("spreadsheetId")

    location_dict = {key: address_dict[key] for key in LOCATION_KEYS if key in address_dict}
    features_dict = {key: address_dict[key] for key in FEATURES_KEYS if key in address_dict}
    values_dict = {key: address_dict[key] for key in VALUES_KEYS if key in address_dict}
    metadata_dict = {key: address_dict[key] for key in METADATA_KEYS if key in address_dict}

    self.value_data_list = [
      ValueData(SHEET_ONE_TITLE + "!B1:1", CATEGORY_HEADERS, "ROWS"),
      ValueData(SHEET_ONE_TITLE + "!A2:A", list(location_dict.keys()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!B2:B", list(location_dict.values()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!D2:D", list(features_dict.keys()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!E2:E", list(features_dict.values()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!G2:G", list(values_dict.keys()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!H2:H", list(values_dict.values()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!J2:J", list(metadata_dict.keys()), "COLUMNS"),
      ValueData(SHEET_ONE_TITLE + "!K2:K", list(metadata_dict.values()), "COLUMNS")
  ]
    
    self.format_specs = [
      FormatSpec(GridRange(0, 1, 1, 2), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(0, 1, 4, 5), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(0, 1, 7, 8), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(0, 1, 10, 11), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(1, len(LOCATION_KEYS) + 1, 0, 1), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(1, len(FEATURES_KEYS) + 1, 3, 4), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(1, len(VALUES_KEYS) + 1, 6, 7), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatSpec(GridRange(1, len(METADATA_KEYS) + 1, 9, 10), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      )
    ]

  def update_values(self):
    """Populate spreadsheet with values using spreadsheet.values().batchUpdate()."""

    # Dynamically map ranges and values to body data, maintaining key-value parallelism with dicts
    values_body = {
      "valueInputOption": "RAW",
      "data": [
        {"range": value_data.range, "values": [value_data.values], "majorDimension": value_data.major_dimension} for value_data in self.value_data_list
      ]
    }

    self.gsheet.client.spreadsheets().values().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = values_body
    ).execute()
    print("spreadsheets.values.batchUpdate executed.")

  def repeat_cell_builder(self, sheet_id, format_spec):
    """Formatting requests in the Google Sheets API involve many complex nested arrays.
    This helper function unpacks specifications to fit the necessary structure."""

    grid_range = format_spec.grid_range
    kwargs = format_spec.kwargs
    
    repeat_cell = {
      "repeatCell": {
        "range": {
          "sheetId": sheet_id,
          "startRowIndex": grid_range.start_row,
          "endRowIndex": grid_range.end_row,
          "startColumnIndex": grid_range.start_col,
          "endColumnIndex": grid_range.end_col
        },
        "cell": {"userEnteredFormat": {}},
        "fields": "userEnteredFormat"
      }
    }

    user_format_dict = repeat_cell["repeatCell"]["cell"]["userEnteredFormat"]
    fields_to_append = []

    # Check for dictionaries with kwargs
    if FormatKwarg.BG_COLOR in kwargs:
      user_format_dict["backgroundColor"] = kwargs["bg_color"]
      fields_to_append.append("backgroundColor")
    
    if FormatKwarg.TEXT_COLOR in kwargs:
      if "textFormat" not in user_format_dict:
        user_format_dict["textFormat"] = {}
      user_format_dict["textFormat"]["foregroundColor"] = kwargs["text_color"]
      fields_to_append.append("textFormat.foregroundColor")
    
    # Join fields list into required fields string
    repeat_cell["repeatCell"]["fields"] = "userEnteredFormat(" + ",".join(fields_to_append) + ")"

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
    # start_row, end_row, start_col, end_col are unpacked from "range" tuple; dicts like bg_color are unpacked as kwargs.
    format_body = {
      "requests": [
        self.repeat_cell_builder(sheet_id, spec) for spec in self.format_specs
      ]
    }

    self.gsheet.client.spreadsheets().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")
  
from enum import StrEnum

"""
Populate Google Sheet object with property data by updating values and formatting.
"""


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
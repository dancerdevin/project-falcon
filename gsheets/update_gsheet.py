from gsheets_client import SHEET_ONE_TITLE
from create_gsheet import GoogleSheet
from dataclasses import asdict
import os
import sys

# Locate parent directory to import property data scripts
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from spreadsheets import CellRange, Layout, RowLabelsByBlock, ValuesByBlock
from property_schema import Property

"""
Populate Google Sheet object with property data by updating values and formatting.
"""

# TODO: reconceive this as plug-ins that receive a Property and Layout. Update_values() will need both, update_format just the latter
# update_values() will take Property data and use Selectors by Layout block to populate the right values in the right places
# update_format() will take the Layout and use the All-type Selectors to apply FormatRules and translate them in Gsheets lingo
# build_valuedata() and build_formatdata() could be the plug-in functionality and feed into update_values()/update_format()
# NOTE: due to the layers of refactoring, there may be some unnecessary mediation here, but I think that's OK

# NOTE: I don't THINK that I need this anymore? This feels like too many layers of abstraction as long as I have a plug-in (or remake as plug-in)
class FormatKwarg:
  """Expected kwargs for formatting updates using repeat_cell_builder()."""
  BG_COLOR = "bg_color"
  TEXT_COLOR = "text_color"

# NOTE: I think it's fine to retain this for my own legibility
class ValueData:
  """Data required to update values includes cell range as A1 format string, values, and major_dimension (rows or columns)."""
  def __init__(self, range, values, major_dimension):
    self.range = range
    self.values = values
    self.major_dimension = major_dimension

# NOTE: Let's call this FormatData to distinguish it from FormatSpec/show its paralellism with ValueData
class FormatData:
  """Data required to update format includes cell range in a tuple of ints and FormatKwargs."""
  def __init__(self, grid_range, **kwargs):
    self.grid_range = grid_range
    self.kwargs = kwargs

# TODO: OK. first, use my Selector code to generate CellRanges, then translate into A1 format for ValueData, then grab keys() or values() as values,
# then majorDimension is just whether or not it's the headers on top or not. Then similarly instantiate FormatData with FormatRules using same Selector code.
# So values can just use Selectors to produce lists of CellRanges and format can use FormatRules to add FormatSpecs TO Selector-drived CellRanges. FormatData
# CellRanges can also be asdict-ed straight into what Gsheets wants, I think, because those are not in A1 format.

# TODO: what do I NEED from this still? I don't need all these dicts. I will need to translate ranges into A1 format for values.
# So, like: on the initialization of a PropertyGsheet, build_valuedata and build_formatdata, effectively, FROM the Property, Layout, and Gsheet inputs
class PropertySpreadsheet:
  def __init__(self, prop: Property, layout: Layout):
    headers = list(asdict(prop).keys())
    location_dict = asdict(prop.location)
    features_dict = asdict(prop.features)
    values_dict = asdict(prop.values)
    attr_dict = asdict(prop.attributes)
    metadata_dict = asdict(prop.metadata)

    # Iteratively generate list of ValueData from Property.
    self.value_data_list = [ValueData(SHEET_ONE_TITLE + "!B1:1", headers, "ROWS")]
    prop_dict = asdict(prop)
    # TODO: header value/layout info here

    for k, v in prop_dict.items():
      # k is category/column (e.g., location), v is dict of field/rowname and value.
      # NOTE: OK: here I can use Selectors to grab CellRanges as long as I pass this a Layout, then convert with _col_int_to_char()
      # Find ColumnBlock with rowname, find relevant CellRange with Selector.
      row_name_range_list = RowLabelsByBlock(k).resolve(layout)
      row_name_range = row_name_range_list[0]
      start_col_str = self._col_int_to_char(row_name_range.start_col)
      end_col_str = self._col_int_to_char(row_name_range.end_col)
      range_str = SHEET_ONE_TITLE + f"!{start_col_str}1:{end_col_str}"
      self.value_data_list.append(ValueData(range=range_str, values=list(v.keys()), major_dimension="COLUMNS"))
      value_range_list = ValuesByBlock(k).resolve(layout)
      value_range = value_range_list[0]
      # NOTE: repeat code, consolidate
      start_col_str = self._col_int_to_char(value_range.start_col)
      end_col_str = self._col_int_to_char(value_range.end_col)
      range_str = SHEET_ONE_TITLE + f"!{start_col_str}1:{end_col_str}"
      self.value_data_list.append(ValueData(range=range_str, values=list(v.values()), major_dimension="COLUMNS"))
      

  #   self.value_data_list = [
  #     ValueData(SHEET_ONE_TITLE + "!B1:1", headers, "ROWS"),
  #     ValueData(SHEET_ONE_TITLE + "!A2:A", list(location_dict.keys()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!B2:B", list(location_dict.values()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!D2:D", list(features_dict.keys()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!E2:E", list(features_dict.values()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!G2:G", list(values_dict.keys()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!H2:H", list(values_dict.values()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!J2:J", list(attr_dict.keys()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!K2:K", list(attr_dict.values()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!M2:M", list(metadata_dict.keys()), "COLUMNS"),
  #     ValueData(SHEET_ONE_TITLE + "!N2:N", list(metadata_dict.values()), "COLUMNS")
  # ]
    
    self.format_specs = [
      FormatData(CellRange(0, 1, 1, 2), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(0, 1, 4, 5), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(0, 1, 7, 8), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(0, 1, 10, 11), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(1, len(location_dict) + 1, 0, 1), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(1, len(features_dict) + 1, 3, 4), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(1, len(values_dict) + 1, 6, 7), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      ),
      FormatData(CellRange(1, len(metadata_dict) + 1, 9, 10), 
        **{
          FormatKwarg.BG_COLOR: {"red": 0.4156, "green": 0.6588, "blue": 0.3098},
          FormatKwarg.TEXT_COLOR: {"blue": 1, "red": 1, "green": 1, "alpha": 1}
        }
      )
    ]

  def _col_int_to_char(self, col):
    """Use ASCII numbering to convert column int to letters, e.g., A, AA. Assumes 0-based columns, so adds 1."""
    result = ""
    n = col + 1
    print(f"debug: n is {n}")
    while n > 0:
      n, remainder = divmod(n - 1, 26)
      result = chr(65 + remainder) + result
    print(f"debug: result is {result}")
    return result

class PropertyGsheet:
  """Input PropertySpreadsheet and Gsheet, implement update_values() and update_format() to turn ValueData/FormatData into dicts."""
  def __init__(self, propsheet: PropertySpreadsheet, gsheet: GoogleSheet):
    self.gsheet = gsheet
    self.gsheet_id = gsheet.spreadsheet.get("spreadsheetId")
    self.value_data_list = propsheet.value_data_list
    self.format_specs = propsheet.format_specs

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
  
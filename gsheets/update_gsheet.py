from gsheets_client import SHEET_ONE_TITLE
from create_gsheet import GoogleSheet
from dataclasses import asdict
import os
import sys

# Locate parent directory to import property data scripts
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from spreadsheets import Layout, RowLabelsByBlock, ValuesByBlock, FormatRule, FormatSpec, ColumnHeaders
from property_schema import Property

"""
Populate Google Sheet object with property data by updating values and formatting.
"""

# # NOTE: I don't THINK that I need this anymore? This feels like too many layers of abstraction as long as I have a plug-in (or remake as plug-in)
# class FormatKwarg:
#   """Expected kwargs for formatting updates using repeat_cell_builder()."""
#   BG_COLOR = "bg_color"
#   TEXT_COLOR = "text_color"

class ValueData:
  """Data required to update values includes cell range as A1 format string, values, and major_dimension (rows or columns)."""
  def __init__(self, range, values, major_dimension):
    self.range = range
    self.values = values
    self.major_dimension = major_dimension

# NOTE: Let's call this FormatData to distinguish it from FormatSpec/show its paralellism with ValueData
class FormatData:
  """Data required to update format includes cell range in a tuple of ints and FormatKwargs."""
  def __init__(self, cell_range, **kwargs):
    self.cell_range = cell_range
    self.kwargs = kwargs

class PropertySpreadsheet:
  def __init__(self, prop: Property, layout: Layout):
    self.layout = layout
    prop_dict = asdict(prop)
    headers_list = self._build_gsheets_header_row(prop_dict, layout)
    format_specs = {
      "gr_bg_wh_txt": FormatSpec(text_color="white", bg_color="green")
    }

    # Generate header ValueData and FormatData, then iteratively populate list of ValueData from Property.
    header_range_list = ColumnHeaders().resolve(layout)
    start_col_int = header_range_list[0].start_col
    end_col_int = start_col_int + len(headers_list) - 1 # Headers range must incorporate empty strings for Gsheets
    start_col_str = self._col_int_to_char(start_col_int)
    end_col_str = self._col_int_to_char(end_col_int)
    range_str = SHEET_ONE_TITLE + f"!{start_col_str}1:{end_col_str}"
    self.value_data_list = [ValueData(range=range_str, values=headers_list, major_dimension="ROWS")]
    self.format_data_list = []
    self.format_rules = [FormatRule(format=format_specs["gr_bg_wh_txt"], selector=ColumnHeaders())]

    for k, v in prop_dict.items():
      # k is category/column (e.g., location), v is dict of field/rowname and value.
      # Find ColumnBlock with rowname, find relevant CellRange with Selector.
      row_name_range_list = RowLabelsByBlock(k).resolve(layout)
      start_col_str, end_col_str = self._cellrange_list_to_col_strs(row_name_range_list)
      range_str = SHEET_ONE_TITLE + f"!{start_col_str}2:{end_col_str}"
      self.value_data_list.append(ValueData(range=range_str, values=list(v.keys()), major_dimension="COLUMNS"))
      value_range_list = ValuesByBlock(k).resolve(layout)
      start_col_str, end_col_str = self._cellrange_list_to_col_strs(value_range_list)
      range_str = SHEET_ONE_TITLE + f"!{start_col_str}2:{end_col_str}"
      self.value_data_list.append(ValueData(range=range_str, values=list(v.values()), major_dimension="COLUMNS"))
      # Build the FormatRules here while iterating through the blocks.
      # NOTE: Hard-coding some simple rules for testing.
      self.format_rules.append(FormatRule(format=format_specs["gr_bg_wh_txt"], selector=RowLabelsByBlock(k)))
    
      # Generate FormatData(CellRange, dict)
      for rule in self.format_rules:
        cell_ranges = rule.selector.resolve(layout)
        for cell_range in cell_ranges:
          self.format_data_list.append(FormatData(
            cell_range=cell_range,
            **self._format_spec_to_format_data(rule.format)))

  def _col_int_to_char(self, col):
    """Use ASCII numbering to convert column int to letters, e.g., A, AA. Assumes 0-based columns, so adds 1."""
    result = ""
    n = col + 1
    while n > 0:
      n, remainder = divmod(n - 1, 26)
      result = chr(65 + remainder) + result
    return result
  
  def _cellrange_list_to_col_strs(self, lst):
    """Extracts start_col int from the first element of a list of CellRanges and end_col int from last element."""
    # NOTE: I return one range by referencing the first (leftmost) and last (rightmost) CellRange in the list.
    # But the mere fact that I can do that likely implies I am doing too much work populating a bunch of micro-ranges for each value subset.
    # TODO: Review range generation code and ensure I'm not doing more work than I need to be.
    start_col_int = lst[0].start_col
    start_col_str = self._col_int_to_char(start_col_int)
    end_col_int = lst[-1].end_col
    end_col_str = self._col_int_to_char(end_col_int)
    return start_col_str, end_col_str
  
  def _format_spec_to_format_data(self, formatspec):
    format_data_kwargs = {}
    if formatspec.text_color == "white":
      format_data_kwargs["text_color"] = {"blue": 1, "red": 1, "green": 1, "alpha": 1}
    if formatspec.bg_color == "green":
      format_data_kwargs["bg_color"] = {"red": 0.4156, "green": 0.6588, "blue": 0.3098}
    return format_data_kwargs
  
  def _build_gsheets_header_row(self, prop_dict, layout):
    header_list = []
    for key in prop_dict.keys():
      header_list.append(key)
      offset = layout.block_index[key].width - layout.block_index[key].value_offset
      header_list += [""] * offset
    return header_list

class PropertyGsheet:
  """Input PropertySpreadsheet and Gsheet, implement update_values() and update_format() to turn ValueData/FormatData into dicts."""
  def __init__(self, propsheet: PropertySpreadsheet, gsheet: GoogleSheet):
    self.gsheet = gsheet
    self.gsheet_id = gsheet.spreadsheet.get("spreadsheetId")
    self.value_data_list = propsheet.value_data_list
    self.format_data_list = propsheet.format_data_list

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

  def repeat_cell_builder(self, sheet_id, format_data: FormatData):
    """Formatting requests in the Google Sheets API involve many complex nested arrays.
    This helper function unpacks specifications to fit the necessary structure."""

    cell_range = format_data.cell_range
    kwargs = format_data.kwargs
    
    repeat_cell = {
      "repeatCell": {
        "range": {
          "sheetId": sheet_id,
          "startRowIndex": cell_range.start_row,
          "endRowIndex": cell_range.end_row,
          "startColumnIndex": cell_range.start_col,
          "endColumnIndex": cell_range.end_col
        },
        "cell": {"userEnteredFormat": {}},
        "fields": "userEnteredFormat"
      }
    }

    user_format_dict = repeat_cell["repeatCell"]["cell"]["userEnteredFormat"]
    fields_to_append = []

    # TODO: Consider re-implementing FormatKwargs or if just having the string comparisons here is fine
    if "bg_color" in kwargs:
      user_format_dict["backgroundColor"] = kwargs["bg_color"]
      fields_to_append.append("backgroundColor")
    
    if "text_color" in kwargs:
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
        self.repeat_cell_builder(sheet_id, spec) for spec in self.format_data_list
      ]
    }

    self.gsheet.client.spreadsheets().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")
  
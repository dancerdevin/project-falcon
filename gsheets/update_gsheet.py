from gsheets_client import SHEET_ONE_TITLE
from create_gsheet import GoogleSheet
from dataclasses import asdict
import os
import sys

# Locate parent directory to import property data scripts
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from spreadsheets import CellRange, Layout
from property_spreadsheets import PropertySpreadsheet, ValueData, FormatData
from typing import List, Dict

"""
Populate Google Sheet object with property data by updating values and formatting.
"""

GSHEET_SPECS = {
    "white": {"blue": 1, "red": 1, "green": 1, "alpha": 1},
    "green": {"red": 0.4156, "green": 0.6588, "blue": 0.3098}
}


class PropertyGsheet:
  """Input PropertySpreadsheet and Gsheet, implement update_values() and update_format() to turn ValueData/FormatData into dicts."""
  def __init__(self, propsheet: PropertySpreadsheet, gsheet: GoogleSheet):
    self.gsheet = gsheet
    self.gsheet_id = gsheet.spreadsheet.get("spreadsheetId")
    self.layout = propsheet.layout
    self.value_data_list = self._build_gsheets_padding(propsheet.value_data_list, self.layout)
    self.format_data_list = propsheet.format_data_list

    # For Gsheets update_values() body dicts, pass two big ranges, one including the headers and one not.
    layout_range_with_headers = CellRange.get_bounding_range_from_layout(self.layout)
    self.layout_range_with_headers_str = self._cellrange_to_gsheets_string(layout_range_with_headers)
    layout_range_without_headers = CellRange.get_bounding_range_from_layout(self.layout, with_headers=0)
    self.layout_range_without_headers_str = self._cellrange_to_gsheets_string(layout_range_without_headers)
    

  def _cellrange_to_gsheets_string(self, range: CellRange) -> str:
    """Adds sheet name and punctuation required by Google Sheets API for value updates."""
    return SHEET_ONE_TITLE + "!" + range.as_string
  
  def _build_gsheets_padding(self, value_data_list, layout):
    """Adds empty strings to replicate spacing between header strings and between value sublists."""
    updated_value_list = []
    offset_list = []
    for val_i, val in enumerate(value_data_list):
      # NOTE: Arrangement of value_data_list is headers, labels, values, labels, values... so pad inside first element, then pad after even indices.
      if val_i == 0:
        updated_value_sublist = []
        for header_i, header in enumerate(val.values):
          # Interject "" in between elements of the header sublist, the first element of value_data_list, based on the offset between ColumnBlocks.
          # Begin headers with first value_offset (to, e.g., leave A1 empty).
          if header_i == 0:
            offset = layout.block_index[header].value_offset
            updated_value_sublist += [""] * offset

          # All headers should be followed by padding equal the difference between total width and value_offset.
          updated_value_sublist.append(header)
          offset = layout.block_index[header].width - layout.block_index[header].value_offset
          updated_value_sublist += [""] * offset

          # For the rest of value_data_list, the sublists will not be modified: instead, add X number of [""] sublists between ColumnBlocks.
          offset_val_to_append = offset + layout.block_index[header].label_offset - 1 # Assume that label is populated, unlike for headers, so 1 less padding
          offset_list.append(offset_val_to_append) if offset_val_to_append > 0 else offset_list.append(0)

        updated_value_list.append(updated_value_sublist)

      elif val_i % 2 == 0:
        updated_value_list.append(val.values)
        offset = offset_list.pop(0) # Return first element and remove from offset_list
        updated_value_list += [[""]] * offset # Add however much padding is necessary as sublists after adding the values

      else:
        updated_value_list.append(val.values)

    return updated_value_list

  def update_values(self):
    """Populate spreadsheet with values using spreadsheet.values().batchUpdate()."""

    # Dynamically map ranges and values to body data, maintaining key-value parallelism with dicts
    # NOTE: Presumes that the first element of value_data_list is the headers, which will be the only dataset presented as "ROWS".
    values_body = {
      "valueInputOption": "RAW",
      "data": [
        {
          "range": self.layout_range_with_headers_str,
          "values": [self.value_data_list.pop(0)],
          "majorDimension": "ROWS"
        },
        {
          "range": self.layout_range_without_headers_str,
          "values": self.value_data_list,
          "majorDimension": "COLUMNS"
        }
      ]
    }

    self.gsheet.client.spreadsheets().values().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = values_body
    ).execute()
    print("spreadsheets.values.batchUpdate executed.")

  def _repeat_cell_list_builder(self, sheet_id, format_data: FormatData) -> List[Dict]:
    """Formatting requests in the Google Sheets API involve many complex nested arrays. This helper function unpacks specifications to fit the necessary structure.
    Because FormatData may select multiple ranges to apply the same specification, returns a list of 'repeat_cell' dictionaries to be cumulatively appended to
    one big list that update_format() iterates through."""

    ranges = format_data.range
    kwargs = format_data.spec

    repeat_cell_list = []
    for range in ranges:
      
      repeat_cell = {
        "repeatCell": {
          "range": {
            "sheetId": sheet_id,
            "startRowIndex": range.start_row,
            "endRowIndex": range.end_row,
            "startColumnIndex": range.start_col,
            "endColumnIndex": range.end_col
          },
          "cell": {"userEnteredFormat": {}},
          "fields": "userEnteredFormat"
        }
      }

      user_format_dict = repeat_cell["repeatCell"]["cell"]["userEnteredFormat"]
      fields_to_append = []

      # TODO: As formatting options proliferate, define and call relevant helper functions to do the work below
      if "bg_color" in kwargs:
        user_format_dict["backgroundColor"] = GSHEET_SPECS[kwargs["bg_color"]]
        fields_to_append.append("backgroundColor")
      
      if "text_color" in kwargs:
        if "textFormat" not in user_format_dict:
          user_format_dict["textFormat"] = {}
        user_format_dict["textFormat"]["foregroundColor"] = GSHEET_SPECS[kwargs["text_color"]]
        fields_to_append.append("textFormat.foregroundColor")
      
      # Join fields list into required fields string
      repeat_cell["repeatCell"]["fields"] = "userEnteredFormat(" + ",".join(fields_to_append) + ")"

      repeat_cell_list.append(repeat_cell)

    return repeat_cell_list

  def update_format(self):
    """# Format spreadsheet using spreadsheet.batchUpdate(). First get sheet ID"""
    sheet_id = None
    
    for sheet in self.gsheet.spreadsheet["sheets"]:
      if sheet["properties"]["title"] == SHEET_ONE_TITLE:
        sheet_id = sheet["properties"]["sheetId"]
    if sheet_id is None:
      raise Exception("Error: No match with sheet title found.")

    # Dynamically map ranges, formatting, and fields to format requests
    # Because FormatData may apply the same spec to multiple discontiguous ranges, populate a list of repeat_cell dicts, then iterate for Gsheets requests.
    repeat_cell_list = []
    for fmt in self.format_data_list:
      repeat_cell_list += self._repeat_cell_list_builder(sheet_id, fmt)
    format_body = {
      "requests": [
        repeat_cell_list
      ]
    }

    self.gsheet.client.spreadsheets().batchUpdate(
      spreadsheetId = self.gsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")
  
from dataclasses import dataclass
from typing import Protocol

# NOTE: create Spreadsheet class to hold format information and take data like Property objects (or Locale objects?)
# NOTE: functionality to interface with json files using json_loading.py that can be swapped out for a future database

"""An overexplanation of a spreadsheet schema in my own words for my own sake:

A spreadsheet is typically structured in terms of 1) its values, AKA what's in it, 2) its layout, AKA where values go, and
3) its format, AKA how those look. A layout does not need to know exactly what the kind of thing the values are (like a
Property object), so it remains flexible, but it does need to know how many columns and rows there will have to be,
so I should ensure via an interface that the values are containers, the contents of which can be enumerated.

Different parts of a given layout may have different formatting: for example, I may want to make the header row one
background color (say, green) and the columns below a different background color (say, blue). I can accomplish this with
a 'format rule,' which takes 1) a format specification (like 'green background') and 2) an interface, here called Selector,
designed to find the cell range on a particular grid that corresponds to where the correct PART of the layout is going to be.
For example, a Selector finds a given column's index by its name and the format rule then says 'take a given format spec, like
blue background, and apply it to that range, wherever it is.' In sum, the layout abstractly represents the whole and the Selector
is built to find where consistently relevant parts of that whole are going to be on a given grid and apply the right formatting.
This enables, e.g., passing in new values and using the same Layout objects and format rules to dynamically adapt to different
grid ranges required to fit the new values, which may have a different number of subattributes with different numbers of fields.

I have a very minimal values-layout interface, LayoutSource, because any input error, like a column name having no subattribute 
referent or a subattribute not having fields that can be enumerated, will be blatant and obvious at runtime when build_layout() is 
called. An Selector interface between layout and format 'turns visual bugs into structural failures': what could be a subtle 
problem that might not throw an error or even be executed for a long time can be detected early by ensuring, e.g., that format
specs and rules express intent without trying to assert geometry and do the layout's job for it."""


class LayoutSource(Protocol):
  """Confirm that input is a bundle, i.e., has an extract() method that returns a dict of str keys and dict values."""
  def extract(self, values) -> dict[str, dict]: ...


@dataclass(frozen=True)
class CellRange:
  """Grid primitive, API agnostic"""
  start_row: int
  end_row: int
  start_col: int
  end_col: int


@dataclass
class Layout:
  """Major dimensions (columns and rows)"""
  column_names: list[str]
  column_index: dict[str, int]
  row_names: list[str] # Attribute-oriented data, not row number oriented
  row_index: dict[str, int]
  header_rows: int


def build_layout(values: LayoutSource) -> Layout:
  """Design a dynamic layout with a row for every subattribute, e.g., for every field in a Property's LocationDetails."""
  col_names = []
  row_names = []
  for col, row_dict in values.items():
    # Every key in the values dict represents a column
    col_names.append(col)
    for key in row_dict.keys():
      # Every key in the nested dict represents an attribute/row name
      row_names.append(key)

  # NOTE: I accidentally wrote the below code when I expected build_layout() to receive a Property object,
  # forgetting that I already planned to send a bundle instead.
  # Populate row_names by iterating through the names of fields within in the values Dataclass.
  # cols = values.col_names
  # for col in cols:
  #   subattr = getattr(values, col)
  #   # Validate at this runtime stage that the LayoutSource contains dataclasses that can be enumerate.
  #   if not is_dataclass(subattr):
  #     raise TypeError("Error: a column name in col_names is not a dataclass stored within the input.")
    
  #   for field in fields(subattr):
  #     if field.name not in row_names:
  #       row_names.append(field.name)

  return Layout(
    header_rows = 1,
    col_names = col_names,
    col_index = {name: i for i, name in enumerate(col_names)}, # The Selector will look up index by name, so reverse enumerate
    row_names = row_names
  )


class Selector(Protocol):
  """A Selector interface resolves an abstract layout into a specific cell range on a particular grid."""
  def resolve(self, layout: Layout) -> CellRange: ...


@dataclass(frozen=True)
class FormatSpec:
  """Formatting model to express formatting intent, e.g., font, background"""
  text_color: str
  bg_color: str


@dataclass(frozen=True)
class FormatRule:
  """A 'rule' for formatting combines a given spec with a given layout via a Selector interface.
  E.g., """
  selector: Selector
  format: FormatSpec

"""SELECTORS: Map semantic regions (e.g., columns referenced by name) to particular grid ranges."""

@dataclass(frozen=True)
class HeaderRow:
  """A header row Selector resolves into a CellRange that is header_rows deep and col_names wide."""
  def resolve(self, layout: Layout) -> CellRange:
    return CellRange(
      start_row = 0,
      end_row = layout.header_rows,
      start_col = 0,
      end_col = len(layout.col_names)
    )
  
@dataclass(frozen=True)
class ColumnByName:
  """A column Selector resolves into a CellRange that is row_names deep and one column wide."""
  name: str
  
  def resolve(self, layout: Layout) -> CellRange:
    col = layout.col_index[self.name] # Look up a column's index by name, previously paired by enumerate()
    return CellRange(
      start_row = layout.header_rows,
      end_row = layout.header_rows + len(layout.row_names), # Range is as deep as there are value subattributes
      start_col = col,
      end_col = col + 1 # It's literally one column
    )
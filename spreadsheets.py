from dataclasses import dataclass, asdict
from typing import Protocol, Sequence
from property_schema import Property

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
specs and rules express intent without trying to assert geometry and do the layout's job for it.

Now, a twist: I'm presenting not traditional tabular data but a layout-based document, which arrays subsets of different columns
with different row/field names across a grid. I'm thus going to try to think in terms of 'blocks' that contain a column header
and contents, row names that differ by column to the left of the contents, and padding. To build a layout will then be to build
a column block for however many columns there are."""


@dataclass(frozen=True)
class CellRange:
  """Grid primitive, API agnostic"""
  start_row: int
  end_row: int
  start_col: int
  end_col: int


@dataclass(frozen=True)
class ColumnBlock:
  """Block containing column name, row names for that column, and padding/offset."""
  name: str
  row_names: list[str]
  label_offset: int # Where the row names go
  value_offset: int # Where the column contents go
  width: int # Includes label, value contents, and then spacing for next block


@dataclass
class Layout:
  """Layout representing the relation between column blocks"""
  blocks: Sequence[ColumnBlock]
  block_index: dict[str, ColumnBlock] # Pair block name and block obj for easy lookup by name
  block_start: dict[str, int] # Pair block name and upper-left index for relative position
  header_rows: int

  # Get total width of layout for, e.g., HeaderRow Selector
  @property
  def total_width(self) -> int:
    return max(self.block_start[block.name] + block.width for block in self.blocks)


def build_block(col_name, values) -> ColumnBlock:
  """Each block represents the column header, row names, contents, and spacing/padding."""

  row_names = list(values.keys()) # The values() are dicts where the keys are row names
  # NOTE: next(iter(values)) would be faster and key reference is implied by dict reference

  return ColumnBlock(
    name = col_name,
    row_names = row_names,
    label_offset = 0,
    value_offset = 1,
    width = 3 # Label + value + spacing
  )


def build_layout(prop: Property) -> Layout:
  """Design a dynamic layout with a block per column, each having variable row depth per number of fields."""
  values = asdict(prop) # Render Property dataclass as nested dict
  blocks = [] # list of block objects
  block_index = {} # Pair block names and block objs for easy Selector lookup
  block_start = {} # Pair block names and upper-left indices for relative positioning

  current_col_index = 0

  for column in values.keys():
    block = build_block(column, values[column])
    blocks.append(block)
    block_index[block.name] = block
    block_start[block.name] = current_col_index
    current_col_index += block.width

  return Layout(
    blocks = blocks,
    block_index = block_index,
    block_start = block_start,
    header_rows = 1
  )


class Selector(Protocol):
  """A Selector interface resolves an abstract layout into a specific cell range on a particular grid."""
  # TODO: List[CellRange]?
  def resolve(self, layout: Layout) -> CellRange: ...


@dataclass(frozen=True)
class FormatSpec:
  """Formatting model to express formatting intent, e.g., font, background"""
  text_color: str
  bg_color: str


@dataclass(frozen=True)
class FormatRule:
  """A 'rule' for formatting combines a given spec with a given layout via a Selector interface."""
  selector: Selector
  format: FormatSpec


"""SELECTORS: Map semantic regions (e.g., columns referenced by name) to particular grid ranges."""


@dataclass(frozen=True)
class HeaderRow:
  """A header row Selector resolves into a CellRange that is header_rows deep and col_names plus spacing wide."""
  def resolve(self, layout: Layout) -> CellRange:
    return CellRange(
      start_row = 0,
      end_row = layout.header_rows,
      start_col = 0,
      end_col = layout.total_width
    )
  
# TODO: Now the Selectors below are finding subsets of ColumnBlocks within the layout

@dataclass(frozen=True)
class RowLabelsByBlock:
  """Select just the row names for a given ColumnBlock found by column name."""
  name: str

  def resolve(self, layout: Layout) -> CellRange:
    col = layout.block_start[self.name] # Look up column index by name
    row_names = layout.block_index[self.name].row_names
    row_len = len(row_names)
    return CellRange(
      start_row = layout.header_rows,
      end_row = layout.header_rows + row_len,
      start_col = col,
      end_col = col + 1
    )


# @dataclass(frozen=True)
# class ColumnContentsByName:
#   """A column contents Selector resolves into a CellRange that is row_names deep and one column wide."""
#   name: str
  
#   def resolve(self, layout: Layout) -> CellRange:
#     col = layout.col_index[self.name] # Look up a column's index by name, previously paired by enumerate()
#     row_names_for_col = layout.row_dict[col].values()
#     return CellRange(
#       start_row = layout.header_rows,
#       end_row = layout.header_rows + len(row_names_for_col), # Range is as deep as there are value subattributes
#       start_col = col,
#       end_col = col + 1
#     )
  

# @dataclass(frozen=True)
# class RowNamesByColumnName:
#   """The names of the row fields will be situated to the left of the column's value contents."""
#   name: str

#   def resolve(self, layout: Layout) -> CellRange:
#     col = layout.col_index[self.name]
#     row_names_for_col = layout.row_dict[col].values()
#     return CellRange(
#       start_row = layout.header_rows,
#       end_row = layout.header_rows + len(row_names_for_col),
#       start_col = col - 1,
#       end_col = col
#     )
from spreadsheets import CellRange, Layout, RowLabelsByBlock, ValuesByBlock, FormatRule, FormatSpec, ColumnHeaders, AllRowLabels, AllValues
from property_schema import Property
from dataclasses import asdict, dataclass
from typing import List

"""Define PropertySpreadsheet from Property and Layout, to be passed to, e.g., PropertyGsheet for publication."""

FORMAT_SPECS = {
  "gr_bg_wh_txt": FormatSpec(text_color="white", bg_color="green")
}

# NOTE: Consider how to handle Selectors that apply only to a specific ColumnBlock rather than to all of them in the Layout. String name as input?
FORMAT_RULES = [
  FormatRule(format=FORMAT_SPECS["gr_bg_wh_txt"], selector=ColumnHeaders()),
  FormatRule(format=FORMAT_SPECS["gr_bg_wh_txt"], selector=AllRowLabels())
]


@dataclass
class ValueData:
  """ValueData stores values (rows or columns) as a list for easy reference, as when populating Gsheets update_values() body[values]."""
  values: List

  @staticmethod
  def value_data_list_builder(prop: Property) -> List["ValueData"]:
    """Transform a Property object into a list of ValueData, beginning with headers, then first ColumnBlock's row_names, then values, etc."""
    prop_dict = asdict(prop)
    value_data_list = [ValueData(values=list(prop_dict.keys()))]
    for inner_dict in prop_dict.values():
      value_data_list.append(ValueData(values=list(inner_dict.keys())))
      value_data_list.append(ValueData(values=list(inner_dict.values())))
    return value_data_list


@dataclass
class FormatData:
  """FormatData stores a FormatRule's FormatSpec as a dict and the CellRange output of applying a FormatRule's Selector to a Layout."""
  range: List[CellRange]
  spec: dict

  @staticmethod
  def format_data_list_builder(layout: Layout, format_rules: List) -> List["FormatData"]:
    format_data_list = []
    for rule in format_rules:
      format_data_list.append(FormatData(
        range_list = rule.selector.resolve(layout),
        spec = asdict(rule.format)
      )
    )
    return format_data_list


class PropertySpreadsheet:
  def __init__(self, prop: Property):
    """Generates a Layout, list of ValueData, and list of FormatData."""
    self.layout = Layout.build_layout(prop)
    self.value_data_list = ValueData.value_data_list_builder(prop)
    self.format_data_list = FormatData.format_data_list_builder(self.layout, FORMAT_RULES)
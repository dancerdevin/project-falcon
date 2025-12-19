"""Renderer test: Property bundle -> Layout/Formatting code -> tuples of cell ranges and format specs"""
from spreadsheets import *
from property_schema import *
from property_level_analysis import *

# TODO: Unleash a combo attack that flows from generating a property object, to passing a bundle from said object,
# to calling build_layout() on said bundle and applying some test format rules, to outputting cell ranges and format specs
# together, thereby demonstrating that they can be associated, which is basically what a real renderer will need to do.

prop_list = build_properties("2025-10-10_12-42-27", "2025-10-22_13-42")

prop_obj = prop_list[0]
assert isinstance(prop_obj, Property), "The elements of the build_properties return should be Property objects"

prop_bundle = prop_list[0].as_bundle(NestedPropertyBundle())
assert isinstance(prop_bundle, dict), "The as_bundle() method on a Property object should return a dict"

test_layout = build_layout(prop_bundle)
# assert len(test_layout.blocks.keys()) > 0, "The column_names list should be populated"

test_spec = FormatSpec(text_color="white", bg_color="green")
# test_rule = FormatRule(format=test_spec, selector=RowLabelsByBlock)
test_rules = [
  FormatRule(format=test_spec, 
             selector=RowLabelsByBlock(name=block.name)) for block in test_layout.blocks
             ] # Select row labels for each block and apply 


def test_resolver(layout, rules) -> list[tuple]:
  resolved_rules = []

  for rule in rules:
    range = rule.selector.resolve(layout)
    resolved_rules.append((range, rule.format))

  return resolved_rules

resolved_rules = test_resolver(test_layout, test_rules)

print(resolved_rules)
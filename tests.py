"""Renderer test: Property bundle -> Layout/Formatting code -> tuples of cell ranges and format specs"""
from spreadsheets import *
from property_schema import *
from property_level_analysis import *

# TODO: Unleash a combo attack that flows from generating a property object, to passing a bundle from said object,
# to calling build_layout() on said bundle and applying some test format rules, to outputting cell ranges and format specs
# together, thereby demonstrating that they can be associated, which is basically what a real renderer will need to do.
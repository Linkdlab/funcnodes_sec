import funcnodes as fn
from funcnodes_span import NODE_SHELF as SPAN_SHELF

# from .report import REPORT_SHELF
from .read_data import READ_SHELF

NODE_SHELF = fn.Shelf(
    nodes=[],
    name="Funcnodes SEC",
    description="The nodes of Funcnodes SEC package",
    subshelves=[READ_SHELF, SPAN_SHELF],
)

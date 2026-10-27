"""Ephemeral selection is scoped to a node tree, independent of stored tie data."""
selected = {}
hovered = {}
preview = {}  # area pointer -> (stroke start, end, cut IDs)
boxes = {}


def of(tree):
    return selected.setdefault(tree.as_pointer(), set())


def clear():
    selected.clear()
    hovered.clear()
    preview.clear()
    boxes.clear()

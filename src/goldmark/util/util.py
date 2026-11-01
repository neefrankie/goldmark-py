
WHITESPACE = ' \t\r\n'

def calc_tab_width(current_column: int) -> int:
    """
    TabWidth calculutes how many spaces are needed to fill next Tab Stop,
    based on current column position. Default grid width is 4.

    It calculates how many characters a tab jumps over.
    The length of tab is not fixed.
    Think of tab as a column alignment operation.
    Draw a grid of 4 columns on your screen.
    At any position you press tab key, it jumps to the end of current column,
    skipping 4, 3, 2, 1 characters.
    """
    return 4 - (current_column % 4)

def trim_right_space_length(source: str) -> int:
    return len(source) - len(source.rstrip(WHITESPACE))
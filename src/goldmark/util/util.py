
WHITESPACE = ' \t\r\n'

def is_url_body(c: int) -> bool:
    # Equal to regex [^<>\x00-\x20]
    return (
        32 < c < 60 # exlucde 0-32
        or 60 < c < 62 # exclude 60 < and 62 >
        or 62 < c < 256
    )

def is_alnum(ch: str) -> bool:
    return (
        '0' <= ch <= '9' # 48~57
        or 'a' <= ch <= 'z' # 97~122
        or 'A' <= ch <= 'Z' # 65~90
    )

def is_alpha(ch: str) -> bool:
    return (
        'a' <= ch <= 'z'
        or 'A' <= ch <= 'Z'
    )

def is_lower_alpha(c: str) -> bool:
    return 'a' <= c <= 'z'

def is_upper_alpha(c: str) -> bool:
    return 'A' <= c <= 'Z'

def is_digit(c: str) -> bool:
    return '0' <= c <= '9'

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
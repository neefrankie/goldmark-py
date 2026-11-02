import unittest

from typing import List, NamedTuple


class Line(NamedTuple):
    start: int
    stop: int
    cols: List[int]

def calc_tab_width(current_column: int) -> int:
    return 4 - (current_column % 4)

def create_line(text: str, start: int):
    newline = text.find('\n', start)
    stop = newline + 1

    char_count = stop - start
    cols = [-1] * char_count

    col = 0
    for i, ch in enumerate(text[start:stop]):
        cols[i] = col
        if ch == '\t':
            col += calc_tab_width(col)
        else:
            col += 1

    return Line(start, stop, cols)

class TestUtil(unittest.TestCase):
    def test_cols(self):
        text = "hello\tworld\nA new line\n"
        #       012345 678901 23456789012

        line = create_line(text, 0)

        expected = Line(
            start=0,
            stop=12,
            cols=[0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13]
        )

        self.assertEqual(line, expected)

if __name__ == '__main__':
    unittest.main()
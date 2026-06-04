"""Parser for Infinity Engine 2DA (2-dimensional array) files."""


class Inf2DA:
    """Parses 2DA text tables used by Infinity Engine games.

    Format:
        2DA V1.0
        <default_value>
               COL1    COL2    COL3
        ROW1   val     val     val
        ROW2   val     val     val
    """

    def __init__(self):
        self._rows: int = 0
        self._cols: int = 0
        self._default: str = ""
        self._col_names: list[str] = []
        self._row_names: list[str] = []
        self._data: list[list[str]] = []

    def parse(self, text: str | bytes) -> bool:
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("latin-1")

        lines = [l for l in text.replace("\r\n", "\n").split("\n") if l.strip()]
        if len(lines) < 3:
            return False

        if not lines[0].strip().startswith("2DA"):
            return False

        self._default = lines[1].strip()

        col_parts = lines[2].split()
        self._col_names = col_parts
        self._cols = len(col_parts)

        self._row_names = []
        self._data = []
        for line in lines[3:]:
            parts = line.split()
            if not parts:
                continue
            self._row_names.append(parts[0])
            row_data = parts[1 : self._cols + 1]
            while len(row_data) < self._cols:
                row_data.append(self._default)
            self._data.append(row_data)

        self._rows = len(self._row_names)
        return True

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def default_value(self) -> str:
        return self._default

    def get_value(self, row: int, col: int) -> str:
        if 0 <= row < self._rows and 0 <= col < self._cols:
            return self._data[row][col]
        return self._default

    def get_row_name(self, row: int) -> str:
        if 0 <= row < self._rows:
            return self._row_names[row]
        return ""

    def get_col_name(self, col: int) -> str:
        if 0 <= col < self._cols:
            return self._col_names[col]
        return ""

    def find_row(self, name: str) -> int:
        name_upper = name.upper()
        for i, rn in enumerate(self._row_names):
            if rn.upper() == name_upper:
                return i
        return -1

    def find_col(self, name: str) -> int:
        name_upper = name.upper()
        for i, cn in enumerate(self._col_names):
            if cn.upper() == name_upper:
                return i
        return -1

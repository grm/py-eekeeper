"""ValueList — key/value lists for game data (classes, races, kits, etc.)."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValueItem:
    index: int
    name: str
    min_value: int = 0


class ValueList:
    """A named list of index/name pairs used for dropdowns and lookups."""

    def __init__(self, name: str = ""):
        self._name: str = name
        self._items: list[ValueItem] = []

    def load(self, path: str | Path, allow_empty: bool = False) -> bool:
        path = Path(path)
        if not path.exists():
            return allow_empty

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return allow_empty

        self._items = []
        for entry in data:
            if isinstance(entry, dict):
                self._items.append(ValueItem(
                    index=entry.get("index", 0),
                    name=entry.get("name", ""),
                    min_value=entry.get("min_value", 0),
                ))
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                self._items.append(ValueItem(index=entry[0], name=entry[1]))

        return True

    def load_from_ids(self, text: str) -> bool:
        """Load from an IDS file (index value pairs, one per line)."""
        self._items = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            parts = line.split(None, 1)
            if len(parts) >= 2:
                try:
                    index = int(parts[0])
                    name = parts[1]
                    self._items.append(ValueItem(index=index, name=name))
                except ValueError:
                    continue
        return len(self._items) > 0

    def save(self, path: str | Path) -> bool:
        path = Path(path)
        data = [{"index": item.index, "name": item.name, "min_value": item.min_value}
                for item in self._items]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except OSError:
            return False

    def get_items(self) -> list[ValueItem]:
        return self._items[:]

    def find_by_index(self, index: int) -> ValueItem | None:
        for item in self._items:
            if item.index == index:
                return item
        return None

    def find_by_name(self, name: str) -> ValueItem | None:
        name_lower = name.lower()
        for item in self._items:
            if item.name.lower() == name_lower:
                return item
        return None

    def add(self, item: ValueItem):
        self._items.append(item)

    def remove(self, index: int):
        self._items = [i for i in self._items if i.index != index]

    def clear(self):
        self._items = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def count(self) -> int:
        return len(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

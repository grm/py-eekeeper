"""WeiDU mod detection — parse weidu.log to discover installed mods."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstalledMod:
    """A single installed mod component from weidu.log."""

    name: str  # mod folder name (e.g., "stratagems")
    component: int  # component number
    language: int  # language index
    description: str  # component description if available


# Pattern for a weidu.log line:
# ~MODNAME/SETUP-MODNAME.TP2~ #LANG #COMPONENT // Description
_LINE_RE = re.compile(
    r"^~([^~]+)~\s+#(\d+)\s+#(\d+)"
    r"(?:\s+//\s*(.*))?$"
)


def parse_weidu_log(path: Path) -> list[InstalledMod]:
    """Parse weidu.log and return list of installed mod components.

    Args:
        path: Path to the weidu.log file.

    Returns:
        List of InstalledMod entries found in the log.
    """
    if not path.exists():
        return []

    mods: list[InstalledMod] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        m = _LINE_RE.match(line)
        if not m:
            continue

        mod_path = m.group(1)  # e.g., "STRATAGEMS/SETUP-STRATAGEMS.TP2"
        language = int(m.group(2))
        component = int(m.group(3))
        description = (m.group(4) or "").strip()

        # Extract mod folder name (part before the first /)
        if "/" in mod_path:
            mod_name = mod_path.split("/", 1)[0]
        elif "\\" in mod_path:
            mod_name = mod_path.split("\\", 1)[0]
        else:
            # Bare filename — use stem without extension
            mod_name = Path(mod_path).stem

        mods.append(InstalledMod(
            name=mod_name,
            component=component,
            language=language,
            description=description,
        ))

    return mods

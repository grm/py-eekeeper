"""Auto-backup for save directories before writing."""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def create_backup(save_dir: Path) -> Path | None:
    """Create a backup of the save directory before writing.

    Uses 1-rotation scheme:
    - save_dir.bak exists? Delete it
    - Copy save_dir to save_dir.bak

    Returns the backup path, or None on failure.
    """
    if not save_dir.is_dir():
        return None

    backup_path = save_dir.parent / (save_dir.name + ".bak")

    try:
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(save_dir, backup_path)
    except OSError as e:
        logger.warning("Failed to create backup at %s: %s", backup_path, e)
        return None

    return backup_path

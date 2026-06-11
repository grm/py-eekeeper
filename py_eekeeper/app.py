"""Main application logic — EEKeeper singleton."""

import logging
import shutil
import struct
from pathlib import Path

from .backup import create_backup
from .config import Config
from .formats.inf_tlk import InfTlk
from .formats.inf_game import InfGame, find_baldur_gam
from .formats.inf_chr import InfChr
from .formats.inf_2da import Inf2DA
from .formats.constants import RESTYPE_SPL, RESTYPE_ITM, RESTYPE_2DA, RESTYPE_IDS
from .resources.resource_manager import ResourceManager
from .resources.value_list import ValueList, ValueItem
from .resources.spell_bitmaps import SpellBitmaps
from .resources.kits import encode_kit_ids_value
from .resources.proficiencies import load_weapprof_items
from .resources.game_lists import load_effect_text_items, load_haterace_items
from .resources.item_info import ItemInfo, parse_item_info


logger = logging.getLogger(__name__)


class EEKeeperApp:
    """Core application logic — manages resources, game data, and state."""

    _instance = None

    @classmethod
    def instance(cls) -> "EEKeeperApp":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.config = Config()
        self.resource_manager = ResourceManager()
        self.tlk = InfTlk()
        self.game: InfGame | None = None
        self.spell_bitmaps: SpellBitmaps | None = None

        # Value lists
        self.vl_class = ValueList("Class")
        self.vl_race = ValueList("Race")
        self.vl_alignment = ValueList("Alignment")
        self.vl_gender = ValueList("Gender")
        self.vl_kit = ValueList("Kit")
        self.vl_racial_enemy = ValueList("Racial Enemy")
        self.vl_enemy_ally = ValueList("Enemy/Ally")
        self.vl_state = ValueList("State")
        self.vl_spells = ValueList("Spells")
        self.vl_items = ValueList("Items")
        self.vl_animations = ValueList("Animations")
        self.vl_profs = ValueList("Proficiencies")
        self.vl_affects = ValueList("Affects")

        self._initialized = False
        self._save_path: str = ""
        self._gam_path: Path | None = None

    def initialize(self) -> bool:
        self.config.read()

        if not self.config.install_path:
            return False

        # Initialize resource manager
        if not self.resource_manager.initialize(
            self.config.install_path,
            ignore_data_versions=self.config.ignore_data_versions,
        ):
            return False

        # Open TLK
        tlk_path = self.config.get_tlk_path()
        if tlk_path.exists():
            self.tlk.open(tlk_path)

        # Load value lists from game resources
        self._load_value_lists()

        # Initialize spell bitmaps
        self.spell_bitmaps = SpellBitmaps(self.resource_manager)

        self._initialized = True
        return True

    def _load_value_lists(self):
        self._load_ids_value_list(self.vl_class, "CLASS")
        self._load_ids_value_list(self.vl_race, "RACE")
        self._load_ids_value_list(self.vl_gender, "GENDER")
        self._load_ids_value_list(self.vl_alignment, "ALIGN", "ALIGNMEN")
        self._load_ids_value_list(self.vl_enemy_ally, "EA")
        self._load_ids_value_list(self.vl_state, "STATE")
        self._load_ids_value_list(self.vl_animations, "ANIMATE")
        self._load_racial_enemies()
        self._load_kits()
        self._load_spells()
        self._load_items()
        self._load_profs()
        self._load_affects()

    def _load_ids_value_list(self, vl: ValueList, *ids_names: str) -> bool:
        for ids_name in ids_names:
            data = self.resource_manager.get_resource(RESTYPE_IDS, ids_name)
            if data and vl.load_from_ids(data.decode("latin-1", errors="replace")):
                return True
        return False

    def _load_racial_enemies(self):
        self.vl_racial_enemy.clear()
        data = self.resource_manager.get_resource(RESTYPE_2DA, "HATERACE")
        if not data:
            return
        for item in load_haterace_items(data, self.tlk.get_string):
            self.vl_racial_enemy.add(item)

    def _load_kits(self):
        self.vl_kit.clear()
        self.vl_kit.add(ValueItem(index=self._encode_kit_ids_value(0x4000), name="No Kit"))

        data = self.resource_manager.get_resource(RESTYPE_2DA, "KITLIST")
        if not data:
            return

        table = Inf2DA()
        if not table.parse(data):
            return

        kit_ids_col = table.find_col("KITIDS")
        name_col = table.find_col("MIXED")
        if name_col < 0:
            name_col = table.find_col("ROWNAME")

        for row in range(table.rows):
            if kit_ids_col < 0:
                continue

            kit_id = self._parse_int(table.get_value(row, kit_ids_col))
            if kit_id is None:
                continue
            kit_value = self._encode_kit_ids_value(kit_id)

            if name_col >= 0:
                name_strref = table.get_value(row, name_col)
                try:
                    strref = int(name_strref)
                    name = self.tlk.get_string(strref) or f"Kit {kit_id:#x}"
                except ValueError:
                    name = name_strref
            else:
                name = table.get_row_name(row)

            if self.vl_kit.find_by_index(kit_value):
                continue

            self.vl_kit.add(ValueItem(index=kit_value, name=name))

    def _parse_int(self, value: str) -> int | None:
        try:
            return int(value, 0)
        except (TypeError, ValueError):
            return None

    def _encode_kit_ids_value(self, kit_id: int) -> int:
        return encode_kit_ids_value(kit_id)

    def _load_spells(self):
        self.vl_spells.clear()
        spell_names = self.resource_manager.get_resource_list(RESTYPE_SPL)
        for name in spell_names:
            friendly = self.get_spell_name(name)
            self.vl_spells.add(ValueItem(index=0, name=self._format_resource_list_name(name, friendly)))

    def _load_items(self):
        self.vl_items.clear()
        item_names = self.resource_manager.get_resource_list(RESTYPE_ITM)
        for name in item_names:
            friendly = self.get_item_name(name)
            self.vl_items.add(ValueItem(index=0, name=self._format_resource_list_name(name, friendly)))

    @staticmethod
    def _format_resource_list_name(res_name: str, friendly: str) -> str:
        return f"{res_name} - {friendly}" if friendly != res_name else res_name

    @staticmethod
    def _parse_resource_list_name(list_name: str) -> tuple[str, str]:
        res_name, sep, friendly = list_name.partition(" - ")
        return res_name, friendly if sep else res_name

    def iter_items(self):
        """Yield (resource_name, display_name) pairs from the loaded item list."""
        for item in self.vl_items:
            yield self._parse_resource_list_name(item.name)

    def has_item(self, res_name: str) -> bool:
        """Return True when the item resource exists in the game data."""
        if not res_name:
            return False
        return self.resource_manager.get_resource(RESTYPE_ITM, res_name) is not None

    def _load_profs(self):
        self.vl_profs.clear()

        data = self.resource_manager.get_resource(RESTYPE_2DA, "WEAPPROF")
        if data:
            for item in load_weapprof_items(data, self.tlk.get_string):
                self.vl_profs.add(item)
            if self.vl_profs.count:
                return

        fallback_profs = [
            (89, "Bastard Sword"),
            (90, "Long Sword"),
            (91, "Short Sword"),
            (92, "Axe"),
            (93, "Two-Handed Sword"),
            (94, "Katana"),
            (95, "Scimitar/Wakizashi/Ninja-To"),
            (96, "Dagger"),
            (97, "War Hammer"),
            (98, "Spear"),
            (99, "Halberd"),
            (100, "Flail/Morning Star"),
            (101, "Mace"),
            (102, "Quarterstaff"),
            (103, "Crossbow"),
            (104, "Longbow"),
            (105, "Shortbow"),
            (106, "Dart"),
            (107, "Sling"),
            (111, "Two-Handed Weapon Style"),
            (112, "Sword and Shield Style"),
            (113, "Single Weapon Style"),
            (114, "Two Weapon Style"),
            (115, "Club"),
        ]
        for prof_id, name in fallback_profs:
            self.vl_profs.add(ValueItem(index=prof_id, name=name))

    def _load_affects(self):
        self.vl_affects.clear()
        for resource_name in ("EFFTEXT", "EFFECTS"):
            data = self.resource_manager.get_resource(RESTYPE_2DA, resource_name)
            if not data:
                continue
            for item in load_effect_text_items(data, self.tlk.get_string):
                self.vl_affects.add(item)
            if self.vl_affects.count:
                return

    def get_spell_name(self, res_name: str) -> str:
        data = self.resource_manager.get_resource(RESTYPE_SPL, res_name)
        if data and len(data) >= 12:
            strref = struct.unpack_from("<I", data, 8)[0]
            name = self.tlk.get_string(strref)
            if name:
                return name
        return res_name

    def get_item_name(self, res_name: str) -> str:
        info = self.get_item_info(res_name)
        if info:
            return info.display_name
        return res_name

    def get_item_info(self, res_name: str) -> ItemInfo | None:
        data = self.resource_manager.get_resource(RESTYPE_ITM, res_name)
        if not data:
            return None
        return parse_item_info(res_name, data, self.tlk.get_string)

    def open_save(self, save_dir: str | Path) -> bool:
        save_dir = Path(save_dir)
        gam_path = find_baldur_gam(save_dir)
        if not gam_path:
            return False

        self.game = InfGame(
            ignore_data_versions=self.config.ignore_data_versions,
            mem_spells_on_save=self.config.mem_spells_on_save,
        )
        if not self.game.read(gam_path):
            self.game = None
            return False

        self._save_path = str(save_dir)
        self._gam_path = gam_path
        return True

    def save_game(self) -> bool:
        if not self.game or not self._gam_path:
            return False

        if self.config.auto_backup and self._save_path:
            save_dir = Path(self._save_path)
            backup_path = create_backup(save_dir)
            if backup_path:
                logger.info("Backup created at %s", backup_path)
            else:
                logger.warning("Backup failed for %s, proceeding with save", save_dir)

        return self.game.write(self._gam_path)

    def save_game_as(self, new_name: str) -> bool:
        if not self.game or not self._save_path:
            return False
        src = Path(self._save_path)
        dest = src.parent / new_name
        if dest.exists():
            return False
        shutil.copytree(src, dest)
        self._save_path = str(dest)
        self._gam_path = find_baldur_gam(dest)
        if not self._gam_path:
            return False
        return self.game.write(self._gam_path)

    def export_character(self, cre_index: int, path: str | Path) -> bool:
        if not self.game:
            return False
        cre = self.game.get_party_cre(cre_index)
        if not cre:
            return False

        chr_file = InfChr(
            ignore_data_versions=self.config.ignore_data_versions,
            mem_spells_on_save=self.config.mem_spells_on_save,
        )
        chr_file.set_creature(cre)
        chr_file.name = self.game.get_party_char_name(cre_index)
        return chr_file.write(path)

    def import_character(self, path: str | Path) -> InfChr | None:
        chr_file = InfChr(
            ignore_data_versions=self.config.ignore_data_versions,
            mem_spells_on_save=self.config.mem_spells_on_save,
        )
        if chr_file.read(path):
            return chr_file
        return None

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def save_path(self) -> str:
        return self._save_path

    @property
    def has_game_loaded(self) -> bool:
        return self.game is not None

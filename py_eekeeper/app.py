"""Main application logic — EEKeeper singleton."""

import struct
from pathlib import Path

from .config import Config
from .formats.inf_tlk import InfTlk
from .formats.inf_game import InfGame
from .formats.inf_chr import InfChr
from .formats.inf_2da import Inf2DA
from .formats.constants import RESTYPE_SPL, RESTYPE_ITM, RESTYPE_2DA, RESTYPE_IDS
from .resources.resource_manager import ResourceManager
from .resources.value_list import ValueList, ValueItem
from .resources.spell_bitmaps import SpellBitmaps


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
        self.vl_animations = ValueList("Animations")
        self.vl_profs = ValueList("Proficiencies")

        self._initialized = False
        self._save_path: str = ""

    def initialize(self) -> bool:
        self.config.read()

        if not self.config.install_path:
            return False

        # Initialize resource manager
        if not self.resource_manager.initialize(self.config.install_path):
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
        self._load_ids_value_list(self.vl_alignment, "ALIGNMEN")
        self._load_ids_value_list(self.vl_enemy_ally, "EA")
        self._load_ids_value_list(self.vl_state, "STATE")
        self._load_ids_value_list(self.vl_animations, "ANIMATE")
        self._load_kits()
        self._load_spells()
        self._load_profs()

    def _load_ids_value_list(self, vl: ValueList, ids_name: str):
        data = self.resource_manager.get_resource(RESTYPE_IDS, ids_name)
        if data:
            vl.load_from_ids(data.decode("latin-1", errors="replace"))

    def _load_kits(self):
        self.vl_kit.clear()
        self.vl_kit.add(ValueItem(index=0, name="No Kit"))

        data = self.resource_manager.get_resource(RESTYPE_2DA, "KITLIST")
        if not data:
            return

        table = Inf2DA()
        if not table.parse(data):
            return

        name_col = table.find_col("MIXED")
        if name_col < 0:
            name_col = table.find_col("ROWNAME")

        for row in range(table.rows):
            row_name = table.get_row_name(row)
            try:
                kit_id = int(row_name) if row_name.isdigit() else row
            except ValueError:
                kit_id = row

            if name_col >= 0:
                name_strref = table.get_value(row, name_col)
                try:
                    strref = int(name_strref)
                    name = self.tlk.get_string(strref) or f"Kit {kit_id}"
                except ValueError:
                    name = name_strref
            else:
                name = row_name

            self.vl_kit.add(ValueItem(index=kit_id, name=name))

    def _load_spells(self):
        self.vl_spells.clear()
        spell_names = self.resource_manager.get_resource_list(RESTYPE_SPL)
        for name in spell_names:
            friendly = self.get_spell_name(name)
            self.vl_spells.add(ValueItem(index=0, name=f"{name} - {friendly}"))

    def _load_profs(self):
        self.vl_profs.clear()
        from .formats.constants import PROF_LARGESWORDS, PROF_SWORDANDSHIELD

        prof_names = [
            (PROF_LARGESWORDS, "Large Swords"),
            (PROF_LARGESWORDS + 1, "Small Swords"),
            (PROF_LARGESWORDS + 2, "Bows"),
            (PROF_LARGESWORDS + 3, "Spears"),
            (PROF_LARGESWORDS + 4, "Blunt Weapons"),
            (PROF_LARGESWORDS + 5, "Spiked Weapons"),
            (PROF_LARGESWORDS + 6, "Axes"),
            (PROF_LARGESWORDS + 7, "Missiles"),
            (PROF_LARGESWORDS + 8, "Greatswords"),
            (PROF_LARGESWORDS + 9, "Daggers"),
            (PROF_LARGESWORDS + 10, "Halberds"),
            (PROF_LARGESWORDS + 11, "Maces"),
            (PROF_LARGESWORDS + 12, "Flails"),
            (PROF_LARGESWORDS + 13, "Hammers"),
            (PROF_LARGESWORDS + 14, "Clubs"),
            (PROF_LARGESWORDS + 15, "Quarterstaffs"),
            (PROF_LARGESWORDS + 16, "Crossbows"),
            (PROF_LARGESWORDS + 17, "Longbows"),
            (PROF_LARGESWORDS + 18, "Shortbows"),
            (PROF_LARGESWORDS + 19, "Single Weapon Style"),
            (PROF_LARGESWORDS + 20, "Two Weapon Style"),
            (PROF_LARGESWORDS + 21, "Two-Handed Style"),
            (PROF_LARGESWORDS + 22, "Sword and Shield Style"),
        ]
        for prof_id, name in prof_names:
            self.vl_profs.add(ValueItem(index=prof_id, name=name))

    def get_spell_name(self, res_name: str) -> str:
        data = self.resource_manager.get_resource(RESTYPE_SPL, res_name)
        if data and len(data) >= 12:
            strref = struct.unpack_from("<I", data, 8)[0]
            name = self.tlk.get_string(strref)
            if name:
                return name
        return res_name

    def get_item_name(self, res_name: str) -> str:
        data = self.resource_manager.get_resource(RESTYPE_ITM, res_name)
        if data and len(data) >= 12:
            strref = struct.unpack_from("<I", data, 8)[0]
            name = self.tlk.get_string(strref)
            if name:
                return name
        return res_name

    def open_save(self, save_dir: str | Path) -> bool:
        save_dir = Path(save_dir)
        gam_path = save_dir / "BALDUR.GAM"
        if not gam_path.exists():
            return False

        self.game = InfGame()
        if not self.game.read(gam_path):
            self.game = None
            return False

        self._save_path = str(save_dir)
        return True

    def save_game(self) -> bool:
        if not self.game or not self._save_path:
            return False
        gam_path = Path(self._save_path) / "BALDUR.GAM"
        return self.game.write(gam_path)

    def export_character(self, cre_index: int, path: str | Path) -> bool:
        if not self.game:
            return False
        cre = self.game.get_party_cre(cre_index)
        if not cre:
            return False

        chr_file = InfChr()
        # Would need to construct a proper CHR from CRE data
        # For now, write the CRE data wrapped in a CHR header
        return chr_file.write(path)

    def import_character(self, path: str | Path) -> InfChr | None:
        chr_file = InfChr()
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

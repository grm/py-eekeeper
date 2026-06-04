# py-eekeeper — Spécification technique

Réécriture Python/PySide6 de [eekeeper-qt](https://github.com/Goddard/eekeeper-qt), éditeur de sauvegardes pour Baldur's Gate Enhanced Edition (et autres jeux Infinity Engine).

## 1. Vue d'ensemble

EE Keeper permet de :
- Ouvrir une sauvegarde (répertoire contenant `BALDUR.GAM`)
- Afficher et éditer les personnages du groupe (in-party et hors-party)
- Modifier stats, sorts, items, proficiencies, couleurs, scripts
- Exporter/importer des personnages (fichiers `.CHR`)
- Naviguer les ressources du jeu (sorts, items) via le système KEY/BIF
- Chercher des chaînes dans `dialog.tlk`
- Sauvegarder les modifications

**Jeux supportés** : Baldur's Gate Enhanced Edition, Baldur's Gate II Enhanced Edition, Icewind Dale Enhanced Edition.

## 2. Stack technique

- **Langage** : Python 3.11+
- **GUI** : PySide6 (Qt6, LGPL)
- **Parsing binaire** : `struct` + `dataclasses`
- **Images** : Pillow (pour BAM/palette → QPixmap)
- **Packaging** : pyproject.toml, hatch ou poetry
- **Cibles** : Linux, macOS

## 3. Architecture des modules

```
py_eekeeper/
├── __init__.py
├── main.py                      # Point d'entrée, QApplication
├── app.py                       # Classe EEKeeper (singleton logique métier)
├── config.py                    # Settings (chemin install, langue, préférences)
├── formats/                     # Parsing des formats binaires Infinity Engine
│   ├── __init__.py
│   ├── constants.py             # Constantes (RESTYPE_*, ITEMTYPE_*, slots, etc.)
│   ├── inf_key.py               # Parser chitin.key (index des ressources)
│   ├── inf_bif.py               # Parser fichiers .bif (archives de ressources)
│   ├── inf_game.py              # Parser BALDUR.GAM (sauvegarde principale)
│   ├── inf_creature.py          # Parser CRE (données créature — le plus gros)
│   ├── inf_chr.py               # Parser .CHR (personnage exporté)
│   ├── inf_tlk.py               # Parser dialog.tlk (table de chaînes)
│   ├── inf_2da.py               # Parser fichiers 2DA (tables texte)
│   ├── inf_bam.py               # Parser/décodeur BAM (sprites/icônes)
│   └── inf_affect.py            # Structure INF_AFF (effets/affects)
├── resources/                   # Gestion des ressources du jeu
│   ├── __init__.py
│   ├── resource_manager.py      # Orchestrateur KEY → BIF → ressource
│   ├── spell_bitmaps.py         # Chargement icônes de sorts
│   ├── pal_image_list.py        # Images avec palette → QPixmap
│   └── value_list.py            # Listes clé/valeur (kits, classes, races...)
├── ui/                          # Interface graphique PySide6
│   ├── __init__.py
│   ├── main_window.py           # Fenêtre principale (menus, tabs)
│   ├── open_saved_game_dialog.py
│   ├── saved_game_widget.py     # Affichage des personnages du groupe
│   ├── character_sheet.py       # Fiche personnage (stats, couleurs, scripts)
│   ├── spell_tab.py             # Onglet sorts connus
│   ├── memorization_tab.py      # Onglet mémorisation
│   ├── proficiencies_tab.py     # Onglet compétences d'armes
│   ├── inventory_tab.py         # Onglet inventaire
│   ├── spell_browser.py         # Navigateur de sorts
│   ├── item_browser.py          # Navigateur d'items
│   ├── value_list_dialog.py     # Éditeur générique de ValueList
│   ├── string_finder_dialog.py  # Recherche dans dialog.tlk
│   ├── installation_dialog.py   # Config chemin d'installation
│   └── save_game_name_dialog.py # Renommer une sauvegarde
├── data/                        # Données embarquées
│   └── kits.dat                 # Liste des kits (remplace Kits.uld)
└── tests/
    ├── __init__.py
    ├── test_inf_key.py
    ├── test_inf_creature.py
    ├── test_inf_game.py
    └── test_inf_2da.py
```

## 4. Formats binaires — Structures de données

Tous les formats sont **little-endian**, **packed** (pas de padding).

### 4.1 chitin.key (`inf_key.py`)

```python
# INF_KEY_HEADER
KEY_HEADER_FORMAT = '<4s4sII'  # signature, version, bif_count, res_count
# puis offset vers les entrées BIF et les entrées Resource

# INF_KEY_BIF (par entrée BIF)
KEY_BIF_FORMAT = '<IIH'  # file_length, filename_offset, filename_length

# INF_KEY_RESOURCE (par ressource)
KEY_RESOURCE_FORMAT = '<8sHI'  # res_name(8), res_type(u16), locator(u32)
# locator: bits[31:20] = bif_index, bits[19:14] = tileset_index, bits[13:0] = resource_index
```

### 4.2 Fichiers BIF (`inf_bif.py`)

```python
# INF_BIF_HEADER
BIF_HEADER_FORMAT = '<4s4sII'  # signature, version, file_entry_count, tileset_count

# INF_BIF_FILEENTRY
BIF_FILEENTRY_FORMAT = '<IIIH'  # locator, offset, size, type
```

### 4.3 BALDUR.GAM (`inf_game.py`)

```python
# INF_GAME (header principal)
GAME_HEADER_FORMAT = '<4s4sI12sI4sIII8sI4sII8s4sIIB19sI72s'
# Champs clés:
#   signature ('GAME'), version ('V2.0')
#   dw_time (300 unités = 1h)
#   dw_gold
#   dw_in_party_char_offset, dw_in_party_char_count
#   dw_out_party_char_offset, dw_out_party_char_count
#   dw_global_var_offset, dw_global_var_count
#   dw_journal_count, dw_journal_offset
#   ch_party_reputation (valeur * 10)
#   dw_after_journal_offset

INF_MAX_CHARACTERS = 6

# INF_GAME_CHARINFO (par personnage)
CHARINFO_FORMAT = '<2sHII12s8sHHHH152s21s139s'
# Champs clés:
#   w_party_position (0xFFFF si hors-party)
#   dw_cre_offset, dw_cre_size
#   sz_area(8), w_player_x, w_player_y, w_view_x, w_view_y
#   sz_name(21 chars, pour le PC)

# INF_GAME_GLOBAL (variable globale)
GAME_GLOBAL_FORMAT = '<32s8si40s'  # name(32), unknown(8), value(i32), unknown(40)
```

### 4.4 CRE — Créature (`inf_creature.py`)

La structure la plus complexe. ~600 octets de header + données variables.

```python
# INF_CRE (header — struct packed)
# Taille: variable selon version, ~724 octets pour v2.2
CRE_HEADER_FIELDS = [
    ('signature',           '4s'),    # "CRE "
    ('version',             '4s'),    # "V2.2"
    ('long_name_strref',    'I'),
    ('short_name_strref',   'I'),
    ('flags',               'I'),     # CRE_FLAG_*
    ('exp_for_killing',     'I'),
    ('exp',                 'I'),
    ('gold',                'I'),
    ('state_flags',         'I'),     # CRE_STAT_*
    ('current_hp',          'H'),
    ('base_hp',             'H'),
    ('animation_id',        'H'),
    ('_unknown1',           '2s'),
    ('metal_color',         'B'),
    ('minor_color',         'B'),
    ('major_color',         'B'),
    ('skin_color',          'B'),
    ('leather_color',       'B'),
    ('armor_color',         'B'),
    ('hair_color',          'B'),
    ('eff_structure',       'b'),     # 0=v1, 1=v2
    ('small_portrait',      '8s'),
    ('large_portrait',      '8s'),
    ('reputation',          'B'),
    ('hide_in_shadows',     'B'),
    ('ac1',                 'h'),
    ('ac2',                 'h'),
    ('ac_mod_crushing',     'h'),
    ('ac_mod_missile',      'h'),
    ('ac_mod_piercing',     'h'),
    ('ac_mod_slashing',     'h'),
    ('thac0',               'b'),
    ('attacks',             'B'),
    ('save_death',          'B'),
    ('save_wands',          'B'),
    ('save_poly',           'B'),
    ('save_breath',         'B'),
    ('save_spells',         'B'),
    ('resist_fire',         'B'),
    ('resist_cold',         'B'),
    ('resist_electricity',  'B'),
    ('resist_acid',         'B'),
    ('resist_magic',        'B'),
    ('resist_magic_fire',   'B'),
    ('resist_magic_cold',   'B'),
    ('resist_slashing',     'B'),
    ('resist_crushing',     'B'),
    ('resist_piercing',     'B'),
    ('resist_missile',      'B'),
    ('detect_illusions',    'B'),
    ('set_traps',           'B'),
    ('lore',                'B'),
    ('open_locks',          'B'),
    ('move_silently',       'B'),
    ('find_traps',          'B'),
    ('pick_pockets',        'B'),
    ('fatigue',             'B'),
    ('intoxication',        'B'),
    ('luck',                'B'),
    # Proficiencies (legacy, BGII uses affects instead)
    ('prof_large_swords',   'B'),
    ('prof_small_swords',   'B'),
    ('prof_bows',           'B'),
    ('prof_spears',         'B'),
    ('prof_axes',           'B'),
    ('prof_missiles',       'B'),
    ('prof_great_swords',   'B'),
    ('prof_daggers',        'B'),
    ('prof_halberds',       'B'),
    ('prof_maces',          'B'),
    ('prof_flails',         'B'),
    ('prof_hammers',        'B'),
    ('prof_clubs',          'B'),
    ('prof_quarterstaffs',  'B'),
    ('prof_crossbows',      'B'),
    ('_unknown2',           '6s'),
    ('tracking',            'B'),
    ('_unknown3',           '32s'),
    ('str_refs',            '400s'),  # 100 x uint32
    ('level_first_class',   'B'),
    ('level_second_class',  'B'),
    ('level_third_class',   'B'),
    ('sex',                 'B'),
    ('strength',            'B'),
    ('strength_bonus',      'B'),
    ('intelligence',        'B'),
    ('wisdom',              'B'),
    ('dexterity',           'B'),
    ('constitution',        'B'),
    ('charisma',            'B'),
    ('morale',              'B'),
    ('morale_break',        'B'),
    ('racial_enemy',        'B'),
    ('morale_recovery_time','H'),
    ('kit',                 'I'),
    ('override_script',     '8s'),
    ('class_script',        '8s'),
    ('race_script',         '8s'),
    ('general_script',      '8s'),
    ('default_script',      '8s'),
    ('enemy_ally',          'B'),
    ('general',             'B'),
    ('race',                'B'),
    ('class_id',            'B'),
    ('specific',            'B'),
    ('gender',              'B'),
    ('object_references',   '5s'),
    ('alignment',           'B'),
    ('global_actor_enum',   'H'),
    ('local_actor_enum',    'H'),
    # ... suite avec offsets des données variables
]

# Données variables (après le header, positionnées par offsets)
# INF_CRE_KNOWNSPELL
CRE_KNOWNSPELL_FORMAT = '<8sHH'  # spell_name(8), level(u16), type(u16)

# INF_CRE_MEMINFO
CRE_MEMINFO_FORMAT = '<HHHHIIIi'
# type(u16), level(u16), num_memorizable(u16), num_memorized(u16),
# ... (offsets internes)

# INF_CRE_MEMSPELL
CRE_MEMSPELL_FORMAT = '<8sI'  # spell_name(8), memorized(u32: 0=no, 1=yes)

# INF_CRE_ITEM
CRE_ITEM_FORMAT = '<8s2sHHHb3s'  # res_name(8), unknown(2), qty1, qty2, qty3, identified, unknown

# INF_CRE_ITEMSLOTS
INF_NUM_ITEMSLOTS = 39
CRE_ITEMSLOTS_FORMAT = '<' + 'H' * INF_NUM_ITEMSLOTS + '4s'  # 39 x uint16 + 4 unknown

# INF_AFF (affect/effect)
AFF_FORMAT = '<IbbbbII8sIHHIIIIIi8s8s'
# type, target_type, power, ... (varies by effect version)
```

Spell types pour le CRE :
```python
INF_CRE_ST_INNATE = 0  # Sorts innés
INF_CRE_ST_WIZARD = 1  # Sorts de mage
INF_CRE_ST_PRIEST = 2  # Sorts de prêtre
INF_CRE_SPELLTYPES = 3  # Nombre total de types
```

### 4.5 CHR — Personnage exporté (`inf_chr.py`)

```python
# INF_CHR (header)
CHR_HEADER_FORMAT = '<4s4s32sII'
# signature("CHR "), version("V2.2"), name(32), cre_offset, cre_size
# Suivi directement des données CRE
CHR_NAME_MAXLEN = 32
```

### 4.6 dialog.tlk (`inf_tlk.py`)

```python
# INF_TLK_HEADER
TLK_HEADER_FORMAT = '<4s4sHI'  # signature("TLK "), version("V1  "), language_id, string_count
# Suivi d'un offset vers les données de strings

# STRINGENTRY (par string)
TLK_ENTRY_FORMAT = '<HII'  # flags(u16), offset(u32), length(u32)
# Le texte est stocké dans un bloc séparé, accédé par offset+length
```

### 4.7 2DA (`inf_2da.py`)

Format texte tabulé :
```
2DA V1.0
<default_value>
       COL1    COL2    COL3
ROW1   val     val     val
ROW2   val     val     val
```
- Première ligne : signature
- Deuxième ligne : valeur par défaut
- Troisième ligne : noms de colonnes
- Lignes suivantes : nom_de_ligne + valeurs séparées par espaces/tabs

### 4.8 BAM — Sprites (`inf_bam.py`)

```python
# INF_BAM_HEADER
BAM_HEADER_FORMAT = '<4s4sHBBI'
# signature("BAM "), version("V1  "), frame_count, cycle_count,
# transparent_index, frames_offset

# INF_BAM_FRAME
BAM_FRAME_FORMAT = '<HHHI'
# width, height, center_x, center_y_and_offset
# bit 31 of offset = RLE flag (1 = compressed)

# INF_BAM_CYCLE
BAM_CYCLE_FORMAT = '<HH'  # frame_index_count, first_frame_index
```

Décodage : palette 256 couleurs (RGBA), puis données pixels (RLE ou raw).

## 5. Constantes clés (`constants.py`)

```python
# Types de ressources (dans chitin.key)
RESTYPE_BMP = 0x0001
RESTYPE_WAV = 0x0004
RESTYPE_BAM = 0x03E8
RESTYPE_MOS = 0x03EC
RESTYPE_ITM = 0x03ED
RESTYPE_SPL = 0x03EE
RESTYPE_BCS = 0x03EF
RESTYPE_IDS = 0x03F0
RESTYPE_CRE = 0x03F1
RESTYPE_2DA = 0x03F4
RESTYPE_BS  = 0x03F9

# Types d'items (pour le navigateur d'items)
ITEMTYPE_MISC1     = 0
ITEMTYPE_AMULET    = 1
ITEMTYPE_ARMOR     = 2
ITEMTYPE_BELT      = 3
ITEMTYPE_BOOTS     = 4
ITEMTYPE_ARROWS    = 5
ITEMTYPE_BRACER    = 6
ITEMTYPE_HELM      = 7
ITEMTYPE_KEY       = 8
ITEMTYPE_POTION    = 9
ITEMTYPE_RING      = 10
ITEMTYPE_SCROLL    = 11
ITEMTYPE_SHIELD    = 12
ITEMTYPE_FOOD      = 13
ITEMTYPE_BULLETS   = 14
ITEMTYPE_BOW       = 15
ITEMTYPE_DAGGER    = 16
ITEMTYPE_MACE      = 17
ITEMTYPE_SLING     = 18
ITEMTYPE_SSWORD    = 19
ITEMTYPE_LSWORD    = 20
ITEMTYPE_HAMMER    = 21
ITEMTYPE_MSTAR     = 22
ITEMTYPE_FLAIL     = 23
ITEMTYPE_DART      = 24
ITEMTYPE_AXE       = 25
ITEMTYPE_QSTAFF    = 26
ITEMTYPE_XBOW      = 27
ITEMTYPE_FIST      = 28
ITEMTYPE_SPEAR     = 29
ITEMTYPE_HALBERD   = 30
ITEMTYPE_BOLTS     = 31
ITEMTYPE_CLOAK     = 32
ITEMTYPE_GOLD      = 33
ITEMTYPE_GEM       = 34
ITEMTYPE_WAND      = 35
ITEMTYPE_CONTAINER = 36
ITEMTYPE_BOOK      = 37
ITEMTYPE_FAMILIAR  = 38
ITEMTYPE_TATTOO    = 39
ITEMTYPE_LENS      = 40
ITEMTYPE_MISC2     = 43
ITEMTYPE_CLUB      = 44
ITEMTYPE_MISC3     = 46
ITEMTYPE_LBOW      = 47
ITEMTYPE_MISC4     = 48
ITEMTYPE_MISC5     = 49
ITEMTYPE_SWORD     = 57  # Greatsword

# Nombre de slots d'inventaire
INF_NUM_ITEMSLOTS = 39

# Flags de créature (CRE_FLAG_*)
CRE_FLAG_LONG_TOOLTIP   = 0x00000001
CRE_FLAG_NO_CORPSE      = 0x00000002
CRE_FLAG_KEEP_CORPSE    = 0x00000004
CRE_FLAG_WAS_FIGHTER    = 0x00000008
CRE_FLAG_WAS_MAGE       = 0x00000010
CRE_FLAG_WAS_CLERIC     = 0x00000020
CRE_FLAG_WAS_THIEF      = 0x00000040
CRE_FLAG_WAS_DRUID      = 0x00000080
CRE_FLAG_WAS_RANGER     = 0x00000100
CRE_FLAG_FALLEN_PALADIN = 0x00000200
CRE_FLAG_FALLEN_RANGER  = 0x00000400
CRE_FLAG_EXPORTABLE     = 0x00000800
CRE_FLAG_HAS_DUALCLASS  = 0x000001F8  # OR de tous les WAS_*

# Flags d'état (state_flags)
CRE_STAT_DEAD           = 0x00000800
CRE_STAT_ACID_DEAD      = 0x00000400
CRE_STAT_FLAME_DEAD     = 0x00000200
CRE_STAT_EXPLODE_DEAD   = 0x00000100
CRE_STAT_STONE_DEAD     = 0x00000080
CRE_STAT_FROZEN_DEAD    = 0x00000040

# Proficiencies (encodage tribble — 3 bits)
def hi_tribble(byte: int) -> int:
    return (byte >> 3) & 0x07

def lo_tribble(byte: int) -> int:
    return byte & 0x07

def make_tribble(lo: int, hi: int) -> int:
    return (hi << 3) | (lo & 0x07)

# Clé XOR pour certaines ressources (64 octets)
XOR_KEY = bytes([...])  # À extraire du code original

# Erreurs
ERR_NONE = 0
```

## 6. Classes principales — Interface publique

### 6.1 `EEKeeper` (app.py) — Singleton logique métier

```python
class EEKeeper:
    # Configuration
    install_path: str          # Chemin du jeu (ex: ~/.local/share/bg2ee/)
    language: str              # "en_US", "fr_FR", etc.
    documents_path: str        # Répertoire des sauvegardes

    # Options
    use_known_spell_limit: bool
    known_spell_limit: int
    use_mem_spell_limit: bool
    mem_spell_limit: int
    mem_spells_on_save: bool
    allow_chr_overwrite: bool
    default_open_singleplayer: bool
    use_grid_lines: bool
    ignore_data_versions: bool

    # Ressources chargées
    inf_key: InfKey            # Index des ressources
    inf_tlk: InfTlk            # Table de strings
    spell_bitmaps: SpellBitmaps
    pal_image_list: PalImageList

    # ValueLists (données de référence)
    vl_spells: ValueList
    vl_class: ValueList
    vl_race: ValueList
    vl_alignment: ValueList
    vl_gender: ValueList
    vl_kit: ValueList
    vl_racial_enemy: ValueList
    vl_enemy_ally: ValueList
    vl_state: ValueList
    vl_animations: ValueList
    vl_profs: ValueList
    vl_affects: ValueList

    # Méthodes publiques
    def initialize(self) -> bool: ...
    def read_settings(self) -> None: ...
    def write_settings(self) -> None: ...
    def load_bif_files(self) -> bool: ...
    def get_res_data(self, res_type: int, res_name: str) -> bytes | None: ...
    def get_spell_name(self, res_name: str) -> str: ...
    def get_item_name(self, res_name: str) -> str: ...
```

### 6.2 `InfKey` (formats/inf_key.py)

```python
class ResInfo:
    name: str
    type: int
    locator: int  # encoded: bif_index + resource_index
    bif_index: int
    resource_index: int

class InfKey:
    def open(self, path: str) -> bool: ...
    def get_res_info(self, res_type: int, res_name: str) -> ResInfo | None: ...
    def get_bif_file(self, bif_index: int) -> InfBifFile | None: ...
    def get_res_data(self, res_type: int, res_name: str) -> bytes | None: ...
    def get_resource_list(self, res_type: int) -> list[ResInfo]: ...
```

### 6.3 `InfBifFile` (formats/inf_bif.py)

```python
class InfBifFile:
    def open(self, path: str, as_override: bool = False) -> bool: ...
    def get_data(self, res_info: ResInfo) -> bytes | None: ...
    def get_data_offset_and_size(self, res_info: ResInfo) -> tuple[int, int] | None: ...
```

### 6.4 `InfGame` (formats/inf_game.py)

```python
@dataclass
class GameCharInfo:
    party_position: int
    cre_offset: int
    cre_size: int
    area: str
    player_x: int
    player_y: int
    name: str

@dataclass
class GameGlobal:
    name: str
    value: int

class InfGame:
    def read(self, path: str) -> bool: ...
    def write(self, path: str) -> bool: ...

    @property
    def party_count(self) -> int: ...
    @property
    def out_of_party_count(self) -> int: ...
    @property
    def party_gold(self) -> int: ...
    @party_gold.setter
    def party_gold(self, value: int) -> None: ...
    @property
    def party_reputation(self) -> int: ...
    @party_reputation.setter
    def party_reputation(self, value: int) -> None: ...

    def get_party_cre(self, index: int) -> InfCreature: ...
    def get_out_of_party_cre(self, index: int) -> InfCreature: ...
    def get_party_char_name(self, index: int) -> str: ...
    def set_party_char_name(self, index: int, name: str) -> None: ...
    def get_globals(self) -> list[GameGlobal]: ...
    def set_globals(self, globals_list: list[GameGlobal]) -> None: ...
    def has_changed(self) -> bool: ...
```

### 6.5 `InfCreature` (formats/inf_creature.py)

```python
@dataclass
class KnownSpell:
    name: str       # ex: "SPWI102"
    level: int
    type: int       # 0=innate, 1=wizard, 2=priest

@dataclass
class MemInfo:
    type: int       # INF_CRE_ST_*
    level: int
    num_memorizable: int
    num_memorized: int

@dataclass
class MemSpell:
    name: str
    memorized: bool

@dataclass
class CreItem:
    res_name: str
    quantity1: int
    quantity2: int
    quantity3: int
    identified: bool

@dataclass
class ProfData:
    id: int         # proficiency ID (affect type)
    value: int      # 0-5 stars

class InfCreature:
    def read(self, data: bytes, charinfo: GameCharInfo = None) -> bool: ...
    def write(self) -> bytes: ...
    def has_changed(self) -> bool: ...

    # Stats de base
    @property
    def strength(self) -> int: ...
    @property
    def dexterity(self) -> int: ...
    # ... (tous les attributs de INF_CRE accessibles en property)

    # Sorts
    def get_known_spell_count(self, spell_type: int) -> int: ...
    def get_known_spells(self, spell_type: int) -> list[KnownSpell]: ...
    def add_known_spell(self, spell_type: int, name: str, level: int) -> bool: ...
    def remove_known_spell(self, spell_type: int, index: int) -> None: ...
    def get_memorization_info(self) -> list[MemInfo]: ...
    def set_memorization_info(self, info: list[MemInfo]) -> None: ...
    def get_memorized_spells(self, spell_type: int) -> list[MemSpell]: ...

    # Items
    def get_items(self) -> list[CreItem]:  # 39 slots
        ...
    def set_items(self, items: list[CreItem]) -> None: ...

    # Proficiencies (via affects pour BGII+)
    def get_profs(self) -> list[ProfData]: ...
    def set_profs(self, profs: list[ProfData]) -> None: ...

    # Affects
    def get_affects(self) -> list: ...
    def set_affects(self, affects: list) -> None: ...

    # Classes
    @property
    def first_class(self) -> int: ...
    @property
    def second_class(self) -> int: ...
    def is_dual_class(self) -> bool: ...
    def is_multi_class(self) -> bool: ...
```

### 6.6 `InfChr` (formats/inf_chr.py)

```python
class InfChr:
    def read(self, path: str) -> bool: ...
    def write(self, path: str) -> bool: ...
    @property
    def name(self) -> str: ...
    @name.setter
    def name(self, value: str) -> None: ...
    def get_creature(self) -> InfCreature: ...
    def has_changed(self) -> bool: ...
```

### 6.7 `InfTlk` (formats/inf_tlk.py)

```python
class InfTlk:
    def open(self, path: str) -> bool: ...
    def get_string(self, index: int) -> str | None: ...
    @property
    def string_count(self) -> int: ...
```

### 6.8 `Inf2DA` (formats/inf_2da.py)

```python
class Inf2DA:
    def parse(self, text: str | bytes) -> bool: ...
    @property
    def rows(self) -> int: ...
    @property
    def cols(self) -> int: ...
    def get_value(self, row: int, col: int) -> str: ...
    def get_row_name(self, row: int) -> str: ...
    def get_col_name(self, col: int) -> str: ...
```

### 6.9 `InfBam` (formats/inf_bam.py)

```python
class InfBam:
    def read(self, data: bytes) -> bool: ...
    def get_frame_count(self) -> int: ...
    def get_frame_dimensions(self, frame: int) -> tuple[int, int]: ...
    def get_frame_image(self, frame: int) -> QPixmap | None: ...
    # Décodage RLE avec palette 256 couleurs
```

### 6.10 `ValueList` (resources/value_list.py)

```python
@dataclass
class ValueItem:
    index: int      # clé numérique
    name: str       # nom affiché
    min_value: int  # valeur min (pour validation)

class ValueList:
    def load(self, path: str, allow_empty: bool = False) -> bool: ...
    def save(self, path: str) -> bool: ...
    def get_items(self) -> list[ValueItem]: ...
    def find_by_index(self, index: int) -> ValueItem | None: ...
    def find_by_name(self, name: str) -> ValueItem | None: ...
    def add(self, item: ValueItem) -> None: ...
    def remove(self, index: int) -> None: ...
```

## 7. Flux d'exécution détaillé

### 7.1 Initialisation

1. `QApplication` créée avec splash screen
2. `EEKeeper.read_settings()` — lit QSettings (chemin jeu, langue, préférences)
3. Si pas de chemin configuré → afficher `InstallationDialog`
4. `InfKey.open(install_path + "chitin.key")` — indexe toutes les ressources
5. Pour chaque BIF référencé : `InfBifFile.open(bif_path)`
6. `InfTlk.open(install_path + "lang/<lang>/dialog.tlk")`
7. Charger les ValueLists depuis les ressources 2DA du jeu + fichiers .dat locaux
8. `SpellBitmaps` et `PalImageList` initialisés
9. Fenêtre principale affichée

### 7.2 Ouverture d'une sauvegarde

1. Utilisateur choisit un répertoire de save via `OpenSavedGameDialog`
2. `InfGame.read(save_path + "/BALDUR.GAM")`
3. Pour chaque personnage in-party (max 6) :
   - Extraire les données CRE depuis le GAM (par offset/taille)
   - `InfCreature.read(cre_data)`
4. Pour chaque personnage hors-party :
   - Idem
5. Afficher la liste des personnages dans `SavedGameWidget`

### 7.3 Édition d'un personnage

1. Sélection d'un personnage → remplit `CharacterSheetWidget`
2. Les onglets (Spells, Proficiencies, Inventory, Memorization) se remplissent
3. Chaque modification marque le personnage comme `has_changed = True`
4. Les ComboBox sont remplies depuis les ValueLists

### 7.4 Sauvegarde

1. `InfGame.write(save_path + "/BALDUR.GAM")`
2. Recalcul de tous les offsets (les CRE modifiés peuvent changer de taille)
3. Réécriture du header GAM + CHARINFO + CRE data + variables + journal

## 8. UI — Layout des fenêtres

### 8.1 Fenêtre principale (`main_window.py`)

```
┌──────────────────────────────────────────────────────┐
│ Menu: File | Edit | Options | Help                   │
├──────────────────────────────────────────────────────┤
│ Toolbar: Open | Save | Save As                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [SavedGameWidget]                                   │
│  - Liste des personnages (scrollbar horizontal)      │
│  - Portrait + nom de chaque personnage               │
│                                                      │
├──────────────────────────────────────────────────────┤
│  Tabs:                                               │
│  ┌─────────┬──────────┬───────────┬──────────┬────┐ │
│  │ Charact.│  Spells  │Memoriz.   │Proficien.│Inv.│ │
│  ├─────────┴──────────┴───────────┴──────────┴────┤ │
│  │                                                 │ │
│  │  [Contenu de l'onglet actif]                    │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 8.2 CharacterSheet (onglet principal)

- **Stats** : STR, DEX, CON, INT, WIS, CHA (SpinBox)
- **Infos** : HP, AC, THAC0, XP, Gold, Level(s)
- **Sauvegardes** : Death, Wands, Poly, Breath, Spells
- **Résistances** : Fire, Cold, Electricity, Acid, Magic, Slashing, Crushing, Piercing, Missile
- **Thief skills** : Open Locks, Find Traps, Pick Pockets, Move Silently, Hide In Shadows, Detect Illusions, Set Traps
- **Couleurs** : Metal, Minor, Major, Skin, Leather, Armor, Hair (ComboBox ou ColorPicker)
- **Infos combat** : Race, Class, Alignment, Gender, Kit, Racial Enemy
- **Scripts** : Override, Class, Race, General, Default

### 8.3 SpellTab

- 3 listes : Known Spells (Wizard, Priest, Innate)
- Boutons : Add, Remove, Add All
- SpellBrowser en popup pour sélectionner
- Filtre par niveau

### 8.4 MemorizationTab

- Table : Type | Level | Max Can Learn
- Boutons : +1, -1, Max+, Max-

### 8.5 ProficienciesTab

- Table : Proficiency Name | Stars (0-5)
- Affichage conditionnel selon la classe

### 8.6 InventoryTab

- Table des 39 slots : Icon | Item Name | Qty
- ItemBrowser pour sélectionner un item
- Boutons : Set, Remove

## 9. Gestion des fichiers de données

### 9.1 Chemin des sauvegardes

- **Linux** : `~/.local/share/bg2ee/save/` (ou `mpsave/`)
- **macOS** : `~/Documents/Baldur's Gate - Enhanced Edition/save/`

### 9.2 Chemin d'installation du jeu

- **Linux** : `~/.local/share/Steam/steamapps/common/Baldur's Gate Enhanced Edition/`
- **macOS** : `~/Library/Application Support/Steam/steamapps/common/Baldur's Gate Enhanced Edition/`

### 9.3 Structure d'un répertoire de save

```
000000001-Quick-Save/
├── BALDUR.GAM     # Fichier principal de sauvegarde
├── BALDUR.bmp     # Screenshot
└── *.ARE          # Fichiers de zones (optionnel)
```

## 10. Plan d'implémentation (ordre recommandé)

### Phase 1 — Couche formats (parsing binaire)
1. `constants.py` — toutes les constantes
2. `inf_2da.py` — le plus simple, parsing texte
3. `inf_tlk.py` — lecture simple, accès par index
4. `inf_key.py` — index des ressources
5. `inf_bif.py` — extraction de données depuis les archives
6. `inf_creature.py` — le gros morceau
7. `inf_game.py` — orchestration de la sauvegarde
8. `inf_chr.py` — wrapper simple autour de creature
9. `inf_bam.py` — décodage d'images
10. `inf_affect.py` — structures d'effets

### Phase 2 — Couche ressources
1. `resource_manager.py` — facade KEY+BIF
2. `value_list.py` — listes de données
3. `spell_bitmaps.py` — icônes
4. `pal_image_list.py` — images palette

### Phase 3 — Logique métier
1. `config.py` — settings
2. `app.py` — orchestrateur EEKeeper

### Phase 4 — Interface graphique
1. `main_window.py` — squelette
2. `open_saved_game_dialog.py`
3. `saved_game_widget.py`
4. `character_sheet.py`
5. `spell_tab.py` + `spell_browser.py`
6. `memorization_tab.py`
7. `proficiencies_tab.py`
8. `inventory_tab.py` + `item_browser.py`
9. `value_list_dialog.py` + `value_item_dialog.py`
10. `string_finder_dialog.py`
11. `installation_dialog.py`
12. `save_game_name_dialog.py`

### Phase 5 — Tests et polish
1. Tests unitaires sur le parsing
2. Tests d'intégration avec de vraies sauvegardes
3. Packaging (pyproject.toml, entry_points)
4. Documentation utilisateur

## 11. Différences avec l'original

- **Pas de QDataStream** : les ValueLists seront stockées en JSON ou format texte simple
- **Pas de registre Windows** : QSettings avec fichier INI standard
- **Override directory** : géré de la même façon (fichiers en vrac qui overrident les BIF)
- **Proficiencies** : le code utilise les affects pour BGII (pas les champs legacy du header CRE)
- **Unicode** : support natif Python (l'original galère avec les encodages)

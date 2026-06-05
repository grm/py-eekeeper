# Comparaison exhaustive entre eekeeper-qt et py-eekeeper

## 1. Périmètre de comparaison

Ce rapport compare :

- l'ancienne application C++/Qt **eekeeper-qt**, analysée depuis le dépôt amont [Goddard/eekeeper-qt](https://github.com/Goddard/eekeeper-qt) cloné localement dans `/tmp/eekeeper-qt` au commit `41b612e` ;
- l'implémentation Python/PySide6 **py-eekeeper**, analysée sur l'état courant du working tree de ce dépôt.

Le dépôt Python contient des modifications non commitées au moment de l'analyse, notamment dans les parsers de formats, la gestion des ressources, l'UI inventaire et les tests. Le rapport décrit donc l'état réel observé dans les fichiers, pas seulement la documentation.

L'ancien projet Qt n'est pas présent directement dans le dépôt Python. La comparaison repose sur le code source amont C++/Qt, sur `SPEC.md`, sur `README.md`, sur le code Python actuel et sur l'exécution de la suite de tests Python.

---

## 2. Synthèse exécutive

`py-eekeeper` reprend correctement la direction générale de `eekeeper-qt` : même domaine fonctionnel, même logique d'ouverture d'une sauvegarde `BALDUR.GAM`, même dépendance aux ressources Infinity Engine (`KEY/BIF/TLK/2DA/BAM`), et même objectif d'éditer les personnages contenus dans une sauvegarde.

La différence principale est que l'ancien `eekeeper-qt` est un port C++/Qt partiel mais relativement dense de la logique Shadow Keeper, avec beaucoup de code historique, de structures binaires et de dialogues prévus. La version Python est plus petite, plus testable, plus lisible et mieux isolée en modules, mais elle ne couvre pas encore toute la surface applicative visible ou prévue dans l'ancien Qt.

Les parsers Python sont déjà proches de la parité sur plusieurs formats critiques : `GAM`, `CRE`, `CHR`, `KEY`, `BIF`, `TLK`, `2DA`, `BAM`, `AFF`. La plus grosse avance Python est la présence de tests automatisés. Le plus gros retard Python est dans l'interface avancée : pas de vrais navigateurs d'items/sorts, pas d'éditeur de variables globales/journal/affects génériques, import `.CHR` non intégré à la sauvegarde, pas de `Save As`, et plusieurs dialogues existent mais ne sont pas branchés.

---

## 3. État global des deux projets

| Domaine | eekeeper-qt C++/Qt | py-eekeeper Python/PySide6 |
|---|---|---|
| Langage | C++ | Python 3.11+ |
| Toolkit UI | Qt Widgets, qmake, Qt5 cible | PySide6 / Qt6 |
| Packaging | qmake, Flatpak KDE 5.15 | `pyproject.toml`, hatchling, script `py-eekeeper` |
| Plateformes annoncées | Windows, Linux, macOS | Linux, macOS |
| Tests automatisés | Aucun test trouvé | `pytest`, 43 tests dont 42 passent localement |
| Architecture | Globals et singletons historiques | Modules `formats`, `resources`, `ui`, `app`, `config` |
| UI | Nombreux dialogues `.ui`, certains stubs | UI plus compacte, plusieurs dialogues orphelins |
| Moteur formats | Très complet pour l'époque | Déjà substantiel et plus testable |
| Maturité fonctionnelle | Édition partielle, beaucoup de logique historique | Édition partielle, meilleure base de validation |

---

## 4. Arborescence et organisation

### 4.1 eekeeper-qt

L'ancien projet est organisé autour de :

- `EEKeeperQt.pro` : projet qmake principal ;
- `EEKeeper/main.cpp` : point d'entrée ;
- `EEKeeper/EEKeeperQt.cpp` et `EEKeeper/include/EEKeeperQt.h` : singleton applicatif, variables globales, chargement des ressources ;
- `EEKeeper/Inf*.cpp` et `EEKeeper/include/Inf*.h` : parsers de formats Infinity Engine ;
- `EEKeeper/ui/*.cpp`, `EEKeeper/ui/*.h` et `EEKeeper/ui/{linux,mac,win32}/*.ui` : widgets et fichiers UI par plateforme ;
- `res/` et `eekeeper.qrc` : icônes embarquées ;
- `res/lang/en_US/*.uld` et `KitLists/Kits.uld` : listes utilisateur au format Qt binaire.

L'ancien Qt duplique les fichiers `.ui` pour Linux, macOS et Windows. Cela donne une certaine adaptation plateforme, mais augmente fortement le coût de maintenance.

### 4.2 py-eekeeper

La version Python est organisée autour de :

- `py_eekeeper/main.py` : point d'entrée ;
- `py_eekeeper/app.py` : singleton `EEKeeperApp` et orchestration ;
- `py_eekeeper/config.py` : configuration via `QSettings` ;
- `py_eekeeper/formats/` : parsers binaires ;
- `py_eekeeper/resources/` : façade de ressources jeu ;
- `py_eekeeper/ui/` : interface PySide6 ;
- `tests/` : tests unitaires et intégration synthétique.

Cette organisation est plus nette que l'ancien Qt : les formats, les ressources et l'UI sont mieux séparés. En revanche, la spécification `SPEC.md` décrit encore des fichiers ou comportements qui ne sont pas tous présents dans le code actuel, par exemple `pal_image_list.py`, `spell_browser.py`, `item_browser.py` ou `data/kits.dat`.

---

## 5. Build, installation et dépendances

### 5.1 Ancien Qt

`eekeeper-qt` utilise qmake via `EEKeeperQt.pro`. Il dépend de Qt Widgets et compile un exécutable `EEKeeperQt`. Les ressources graphiques sont embarquées avec `eekeeper.qrc`.

Il existe aussi un `flatpak.json` visant un runtime KDE/Qt 5.15. Cela donne une piste de distribution Linux, mais le projet ne contient pas de pipeline CI ni de tests associés.

### 5.2 Python

`py-eekeeper` utilise `pyproject.toml` avec `hatchling`. Les dépendances runtime déclarées sont :

- `PySide6>=6.5` ;
- `Pillow>=10.0`.

Observation importante : `Pillow` est déclaré, mais l'implémentation actuelle du chargement BAM/icône passe surtout par `QImage`/`QPixmap`. Le rôle réel de Pillow semble donc faible ou obsolète dans l'état courant.

La commande exposée est :

```bash
py-eekeeper
```

---

## 6. Configuration et persistance

### 6.1 Points communs

Les deux implémentations conservent l'idée d'une configuration persistante contenant :

- le chemin d'installation du jeu ;
- la langue ;
- le chemin des documents / sauvegardes ;
- des options d'éditeur comme les limites de sorts, l'écriture des sorts mémorisés, l'ignorance des versions de données.

### 6.2 Différences

| Sujet | eekeeper-qt | py-eekeeper |
|---|---|---|
| Système de settings | `QSettings("EEKeeper", ...)` historique | `QSettings("EEKeeper", "py-eekeeper")` |
| Chemin install | manuel, auto-détection stubbée | dialogue avec auto-détection Steam Linux/macOS |
| Chemin documents | stocké dans les settings | stocké, avec defaults Linux/macOS |
| Options spell limits | persistées mais peu ou pas appliquées | persistées mais non appliquées dans l'UI actuelle |
| Overwrite CHR/CRE | persiste, peu ou pas branché | `allow_chr_overwrite` persiste mais non utilisé |
| Grille UI | setting présent | setting présent mais non appliqué |
| Ignore versions | utilisé dans les parsers | propagé aux parsers |
| Réinitialisation à chaud | partielle | changement install demande un redémarrage |

La version Python améliore l'auto-détection d'installation par rapport à l'ancien Qt, surtout sur Linux/macOS. En revanche, plusieurs options héritées existent dans la configuration sans effet visible dans l'interface.

---

## 7. Chargement des ressources jeu

### 7.1 eekeeper-qt

Le chargement historique suit globalement cette séquence :

1. ouvrir `dialog.tlk` dans `lang/<lang>/dialog.tlk` ;
2. lire `chitin.key` ;
3. ouvrir les BIF référencés ;
4. scanner `override/` ;
5. charger les icônes de sorts via BAM ;
6. lire des ressources IDS et 2DA ;
7. construire les listes de classes, races, alignements, kits, proficiencies, sorts, etc. ;
8. charger des listes `.uld` comme `Kits.uld` et `Affects.uld`.

Le modèle C++ repose beaucoup sur des variables globales : `_infKey`, `_infTlk`, `_spellBitmaps`, `_vlClass`, `_vlRace`, `_vlKit`, `_vlAffects`, etc.

### 7.2 py-eekeeper

La version Python centralise davantage dans :

- `ResourceManager` pour `KEY -> BIF -> resource` ;
- `EEKeeperApp` pour l'orchestration ;
- `ValueList` pour les listes d'affichage ;
- `SpellBitmaps` pour les icônes BAM.

Le `ResourceManager` scanne `override/`, donne la priorité aux fichiers override, puis retombe sur les BIF. Il sait exposer une liste de ressources par type.

### 7.3 Différences constatées

| Sujet | eekeeper-qt | py-eekeeper |
|---|---|---|
| Priorité `override/` | Oui | Oui |
| KEY/BIF | Oui | Oui |
| TLK | Oui | Oui |
| IDS chiffrés XOR | Oui | Oui pour 2DA/IDS selon parser actuel |
| 2DA | Oui | Oui |
| BAM | Oui, images Qt | Oui, pixels/Qt pixmap |
| Spell bitmaps | chargés et prévus UI | chargés mais peu ou pas utilisés dans l'UI |
| Palettes personnage | `CPalImageList` | pas de `pal_image_list.py` observé |
| `.uld` | format binaire Qt | remplacé par `ValueList` JSON/IDS/2DA selon cas |
| `Affects.uld` | présent et éditable | pas de `vl_affects` chargé complètement dans l'UI |

La version Python a un modèle de ressources plus propre, mais elle n'a pas encore branché toute la richesse visuelle et toutes les listes configurables de l'ancien Qt.

---

## 8. Formats binaires supportés

### 8.1 Vue d'ensemble

| Format | eekeeper-qt | py-eekeeper | Commentaire |
|---|---|---|---|
| `chitin.key` / KEY | Lecture | Lecture | Parité fonctionnelle attendue |
| `.bif` / BIF | Lecture | Lecture | Python gère aussi des cas de BAM compressé testés |
| `BALDUR.GAM` | Lecture/écriture | Lecture/écriture | Format critique dans les deux |
| `.cre` / CRE embarqué | Lecture/écriture | Lecture/écriture | Cœur de l'éditeur |
| `.chr` | Lecture/écriture parser | Lecture/écriture | Python exporte ; import ne modifie pas encore le party |
| `dialog.tlk` | Lecture | Lecture | Python cache paresseusement les strings |
| `.2da` | Lecture | Lecture | Python teste parsing + XOR |
| `.ids` | Lecture indirecte | Lecture via ressources/listes | Moins exposé explicitement |
| `.bam` | Lecture/décodage | Lecture/décodage | Python teste le décodeur |
| `.bmp` | Ressource/portraits | Ressource/portraits | Python gère portraits de save |
| `.itm` | Lecture pour nom/affichage | Lecture pour nom/affichage | Pas de vrai browser Python |
| `.spl` | Lecture pour nom/affichage | Lecture pour listes de sorts | Pas de vrai browser graphique dédié |
| `.bcs`, `.bs` | Indexés/ressources | Scannés selon types | Pas d'édition |

### 8.2 GAME

Les deux implémentations traitent `BALDUR.GAM` comme le fichier principal d'une sauvegarde :

- personnages in-party ;
- personnages hors-party ;
- or du groupe ;
- réputation du groupe ;
- variables globales ;
- journal ;
- données CRE embarquées.

Différences :

- l'ancien Qt expose surtout les personnages du groupe dans l'UI ; les personnages hors-party sont lus mais peu ou pas manipulables ;
- Python affiche une indication `[NPC]` pour les hors-party dans `SavedGameWidget`, mais l'édition complète hors-party reste à vérifier selon flux UI ;
- Python préserve le journal et les blocs inconnus de façon binaire, sans éditeur ;
- Python expose des API `party_gold`, `party_reputation`, `get_globals`, `set_globals`, mais l'UI ne donne pas encore un éditeur global.

### 8.3 CRE

Le format CRE est le centre des deux applications.

Fonctionnalités communes ou proches :

- statistiques principales ;
- HP, AC, THAC0, XP, or personnel ;
- niveaux ;
- race, classe, genre, alignement, kit ;
- jets de sauvegarde ;
- résistances ;
- compétences voleur ;
- couleurs ;
- portraits ;
- scripts ;
- sorts connus ;
- mémorisation ;
- inventaire ;
- proficiencies via affects pour BG2/EE ;
- effets/affects au niveau modèle.

Différences :

| Sujet | eekeeper-qt | py-eekeeper |
|---|---|---|
| Nombre de slots inventaire | code historique aligné sur 38 slots utiles | constante actuelle `INF_NUM_ITEMSLOTS = 38` dans le code modifié |
| Documentation slots | UI/spec mentionnent parfois 39 | README/SPEC Python mentionnent encore 39 par endroits |
| Affects génériques | parser présent, onglet UI vide | modèle présent, pas d'éditeur UI générique |
| Vitesse | bug observé dans Qt : mauvaise ligne lue | Python modèle `get_speed`/`set_speed`, pas exposé largement |
| Proficiencies | via affects + tribbles dual-class | via affects + constantes Python |
| Sorts mémorisés sans known spell | préservé dans Qt | mécanisme à surveiller/valider en Python |
| Mort / HP | logique historique | Python force HP à 0 si flags de mort selon modèle |

Le code Python semble avoir beaucoup progressé sur la fidélité binaire CRE, mais la surface UI reste plus limitée que le modèle.

### 8.4 CHR

| Sujet | eekeeper-qt | py-eekeeper |
|---|---|---|
| Parser `.CHR` | Oui | Oui |
| Export | prévu / partiellement branché selon UI | Oui via `export_character` |
| Import | objectif historique de remplacement/ajout | lit le `.CHR`, affiche un statut, ne modifie pas encore la sauvegarde |
| Overwrite policy | settings présents | settings présents mais peu utilisés |

L'écart majeur est l'import Python : il parse le personnage, mais ne l'intègre pas encore au `GAM`.

### 8.5 TLK

Les deux versions lisent `dialog.tlk`.

Différences :

- l'ancien Qt utilise le TLK pour afficher les noms et possède un `StringFinderDialog` ;
- Python possède aussi un `StringFinderDialog`, limite les résultats et passe par `InfTlk.get_string` ;
- Python tente UTF-8 puis latin-1, ce qui est plus confortable côté encodage que le C++ historique.

### 8.6 2DA / IDS

Les deux versions utilisent les tables 2DA/IDS pour construire les listes de jeu.

Différences :

- l'ancien Qt construit beaucoup de listes globales depuis `HATERACE`, `WEAPPROF`, `KITLIST`, `ALIGN`, `CLASS`, `RACE`, etc. ;
- Python charge une partie importante des listes, mais `vl_racial_enemy` est instanciée sans chargement complet observé, et `vl_affects` n'est pas équivalente à `Affects.uld`.

### 8.7 BAM / images

Les deux versions savent décoder BAM.

Différences :

- l'ancien Qt utilise les bitmaps de sorts et des mécanismes de palettes pour l'affichage ;
- Python a `SpellBitmaps`, mais les icônes ne sont pas encore branchées dans les onglets de sorts ou d'inventaire ;
- Python n'a pas de `PalImageList` observée alors que la spécification la mentionne.

---

## 9. Interface utilisateur principale

### 9.1 Fenêtre principale

| Élément | eekeeper-qt | py-eekeeper |
|---|---|---|
| Menus File | Open Saved Game, Open Character, Open Creature, Save, Exit prévus | Open Save, Save, Export Character, Import Character, Quit |
| Save As | présent via dialogue/flux historique | absent de la fenêtre principale |
| View | item/spell/creature browsers dockables prévus | absent |
| Tools | pas équivalent strict | String Finder |
| Options / Settings | Installation Directory, listes, options diverses | Installation Directory |
| Help | About/Readme/Website prévus mais incomplets | About |
| Toolbar | Open/Save/Web/About prévus | pas de toolbar équivalente observée |
| Layout | fenêtre + onglets + widgets historiques | splitter vertical + party bar + onglets |

La version Python est plus simple et plus compacte. Elle privilégie les fonctions déjà branchées plutôt que de déclarer beaucoup d'actions non implémentées. En revanche, cela signifie que plusieurs fonctions historiques visibles dans l'ancien Qt n'existent pas encore dans la nouvelle UI.

### 9.2 Ouverture de sauvegarde

**eekeeper-qt** :

- dialogue dédié ;
- liste les saves ;
- exclut Quick-Save / Auto-Save selon comportement observé ;
- supporte single-player, multiplayer et Black Pits ;
- affiche un aperçu `BALDUR.BMP` ;
- évite l'ouverture duplicate.

**py-eekeeper** :

- dialogue dédié ;
- liste `save` et `mpsave` ;
- ouvre les répertoires contenant `BALDUR.GAM` ;
- affiche les personnages dans `SavedGameWidget` ;
- gère les portraits depuis les BMP de sauvegarde ;
- ne semble pas encore couvrir Black Pits explicitement ;
- l'exclusion Quick-Save / Auto-Save doit être vérifiée dans le flux Python actuel.

### 9.3 Barre / sélection de personnages

`eekeeper-qt` utilise un `SavedGameWidget` et crée un `CharacterSheetWidget` par membre in-party. Les NPC/hors-party sont lus mais peu exposés.

`py-eekeeper` possède aussi un `SavedGameWidget`, affiche les personnages et peut indiquer `[NPC]` pour hors-party. La sélection alimente un ensemble fixe d'onglets : Character, Spells, Memorization, Proficiencies, Inventory.

---

## 10. Onglets d'édition personnage

### 10.1 Onglet caractéristiques / fiche personnage

| Champ | eekeeper-qt | py-eekeeper |
|---|---|---|
| Attributs STR/DEX/CON/INT/WIS/CHA | Oui | Oui |
| HP courant/base | Oui | Oui |
| AC | Oui | Oui |
| THAC0 | Oui | Oui |
| XP | Oui | Oui |
| Or personnel | Oui | Oui |
| Niveaux | Oui | Oui |
| Classe/race/genre/alignement | Oui | Oui |
| Kit | Oui | Oui |
| Ennemi racial | Oui | pas exposé clairement |
| Enemy-Ally / General / Specific | Oui côté modèle/UI ancien | pas exposé clairement |
| Vitesse | champ présent mais bug Qt | modèle Python, pas UI évidente |
| Résistances | Oui | Oui |
| Jets de sauvegarde | Oui | Oui |
| Thief skills | Oui | Oui |
| Couleurs | Oui | Oui |
| Portraits | Oui | Oui |
| Scripts | Oui | Oui |
| AC détaillée par type | partielle | pas exposée complètement |
| Morale/fatigue/intox/luck | présent dans CRE | pas exposé largement |

La version Python couvre les champs les plus utiles pour une édition de personnage, mais pas toute la granularité du CRE.

### 10.2 Inventaire

**eekeeper-qt** :

- affiche les slots, noms, quantités, identification ;
- l'inventaire est essentiellement en lecture seule dans l'UI historique observée ;
- l'item browser existe comme widget stub / UI prévue, mais la logique est faible ou absente.

**py-eekeeper** :

- affiche 38 lignes ;
- permet `Set Item` via `QInputDialog.getItem` sur la liste des ITM ;
- permet `Remove` ;
- permet `Identify All` ;
- n'affiche pas d'icônes d'items ;
- ne fournit pas de vrai navigateur graphique avec filtres, catégories, descriptions ;
- affiche les quantités mais ne donne pas une édition riche des charges/quantités.

Python dépasse donc l'ancien Qt sur l'édition basique effective de l'inventaire, mais reste loin d'un item browser complet.

### 10.3 Sorts connus

**eekeeper-qt** :

- onglets Innate/Wizard/Priest ;
- affichage des sorts ;
- quelques actions de mémorisation ;
- ajout/retrait incomplet selon le code UI historique ;
- spell browser prévu mais stubbé.

**py-eekeeper** :

- types Wizard/Priest/Innate ;
- filtre par niveau ;
- listes Known et Available ;
- boutons Add, Add All, Remove, Remove All ;
- noms récupérés via TLK/SPL ;
- pas de browser graphique dédié ;
- pas d'icônes BAM dans l'onglet.

Python est plus utilisable sur l'ajout/retrait de sorts connus, mais n'a pas encore la richesse visuelle prévue.

### 10.4 Mémorisation

**eekeeper-qt** :

- édition des maximums mémorisables par type/niveau ;
- boutons +/- ;
- logique d'écriture avec option de remise à jour des sorts mémorisés.

**py-eekeeper** :

- table Type / Level / Max memorizable ;
- boutons +1, -1, Max +1, Max -1 ;
- pas d'édition détaillée sort par sort des sorts mémorisés ;
- option `mem_spells_on_save` présente côté modèle.

Parité partielle. Les deux se concentrent surtout sur les slots de mémorisation.

### 10.5 Proficiencies

**eekeeper-qt** :

- liste `WEAPPROF` ;
- édition 0-5 ;
- gestion via affects pour BG2/EE ;
- logique dual-class/tribbles historique.

**py-eekeeper** :

- table de 23 proficiencies ;
- édition 0-5 ;
- implémentation via affects ;
- pas de filtrage par classe observé, contrairement à la spécification.

Bonne parité de base. Python est probablement plus simple à tester, mais l'UI est moins contextuelle.

### 10.6 Onglets absents ou incomplets

Dans `eekeeper-qt`, certains onglets ou zones existent mais sont vides ou peu branchés :

- Appearance ;
- Affects ;
- Global Variables ;
- Local Variables ;
- Journal Entries ;
- navigateurs Item/Spell/Creature.

Dans `py-eekeeper`, ces zones ne sont pas encore exposées comme onglets équivalents. Les données sont parfois préservées ou parsées, mais non éditables dans l'UI.

---

## 11. Dialogues auxiliaires

| Dialogue | eekeeper-qt | py-eekeeper | Différence |
|---|---|---|---|
| Installation Directory | Oui, validation Linux inachevée | Oui, auto-détection Steam | Python mieux abouti |
| Open Saved Game | Oui | Oui | Qt couvre davantage de types de saves |
| Save Game Name | Oui, utilisé pour save-as/rename | fichier présent mais non branché | Python incomplet |
| ValueListDialog | Oui, branché pour Kits/Affects | fichier présent mais non branché | Python incomplet |
| ValueItemDialog | Oui | pas observé comme dialogue équivalent autonome | Python incomplet |
| StringFinderDialog | Oui | Oui | Python limite/structure les résultats |
| SpellBrowserWidget | UI/stub | absent | Aucun browser complet |
| ItemBrowserWidget | UI/stub | absent | Aucun browser complet |
| About | prévu/incomplet | Oui simple | Python plus branché |

---

## 12. Fonctionnalités de sauvegarde

### 12.1 Save

Les deux versions savent réécrire `BALDUR.GAM` en recalculant les offsets et en réinjectant les données CRE modifiées.

### 12.2 Save As / renommage

`eekeeper-qt` contient un flux de sauvegarde sous nouveau nom :

- dialogue de nom ;
- numérotation du dossier ;
- copie des fichiers adjacents ;
- écriture du nouveau `BALDUR.GAM`.

`py-eekeeper` ne propose actuellement que `File -> Save` dans la fenêtre principale. `save_game_name_dialog.py` existe mais n'est pas branché.

### 12.3 Fermeture avec modifications

Les deux versions prévoient une vérification de modifications :

- ancien Qt : dialogue Save/Discard/Cancel à la fermeture d'un onglet modifié ;
- Python : dialogue Yes/No/Cancel à la fermeture de l'application si `game.has_changed()`.

---

## 13. Gestion des listes de valeurs

### 13.1 Ancien Qt

`eekeeper-qt` utilise des `CValueList` et des fichiers `.uld` au format binaire Qt `QDataStream`. Exemples :

- `Kits.uld` ;
- `Affects.uld` ;
- `NumAttacks.uld` prévu.

Ces listes peuvent être éditées via les dialogues historiques, au moins pour Kits et Affects.

### 13.2 Python

`py-eekeeper` utilise `ValueList` avec chargement depuis JSON ou formats type IDS/ressources. Les kits sont plutôt construits depuis `KITLIST.2da` et TLK. La spécification mentionne `data/kits.dat`, mais ce fichier n'a pas été observé dans le dépôt.

### 13.3 Différence importante

La version Python ne cherche pas à reproduire le format `.uld` Qt. C'est une bonne simplification technique, mais cela signifie :

- pas de compatibilité directe avec les `.uld` de l'ancien projet ;
- pas d'éditeur d'affects/kits custom branché dans l'UI ;
- une source de vérité davantage tirée des ressources jeu.

---

## 14. Plateformes et chemins

| Sujet | eekeeper-qt | py-eekeeper |
|---|---|---|
| Windows | UI et validation `Baldur.exe` prévues | non annoncé dans README |
| Linux | UI dédiée, validation install stubbée | Linux annoncé, auto-détection Steam |
| macOS | UI dédiée, validation `.app/Contents/Resources` | macOS annoncé, auto-détection Steam |
| Documents | settings et chemins manuels | defaults Linux/macOS |
| Black Pits | dossier `bpsave/` prévu | pas clair / non exposé explicitement |
| Multiplayer saves | `mpsave/` | `mpsave/` |

Python simplifie la cible plateforme en abandonnant Windows pour l'instant. C'est cohérent avec le README, mais c'est une régression de couverture par rapport à l'ancien projet.

---

## 15. Tests et validation

### 15.1 eekeeper-qt

Aucun test unitaire ou intégration automatisés n'a été trouvé. La validation semble essentiellement manuelle.

### 15.2 py-eekeeper

La suite `pytest` contient des tests pour :

- `InfCreature` ;
- `InfGame` ;
- `Inf2DA` ;
- intégration open/edit/save synthétique ;
- formats de ressources (`KEY`, `BIF`, `TLK`, `CHR`, `BAM`, `ResourceManager`) dans un fichier non suivi au moment de l'analyse.

Exécution locale :

```text
42 passed, 1 failed
```

L'échec observé est :

```text
tests/test_integration.py::test_ui_character_sheet_loading
ModuleNotFoundError: No module named 'PySide6'
```

Ce n'est pas un échec fonctionnel du code testé, mais un problème d'environnement : PySide6 n'est pas installé dans l'environnement d'exécution utilisé pour le test.

### 15.3 Différence majeure

La version Python est nettement supérieure sur la testabilité. Elle permet de sécuriser les parsers binaires par des blobs synthétiques et des round-trips. En revanche, il manque encore des tests sur de vraies sauvegardes et ressources de jeu, ce qui est critique pour garantir la parité avec l'ancien outil.

---

## 16. Documentation et spécification

### 16.1 eekeeper-qt

Le projet contient :

- `AUTHORS` ;
- `COPYING` ;
- `TODO` ;
- les licences Qt et Shadow Keeper ;
- peu de documentation utilisateur moderne.

Le `TODO` historique mentionne notamment :

- rendre les navigateurs Item/Spell fonctionnels ;
- charger des CRE/CHR hors-party ;
- changer le portrait ;
- ajouter traductions, About, page web.

### 16.2 py-eekeeper

Le dépôt contient :

- `README.md` ;
- `SPEC.md` ;
- tests ;
- packaging Python.

### 16.3 Écarts entre README/SPEC et code Python

| Sujet documenté | État observé |
|---|---|
| `Full inventory editor (39 equipment slots)` | code actuel aligné plutôt 38 slots ; édition basique, pas full browser |
| `Export/import characters` | export OK, import parse seulement et ne modifie pas le party |
| `spell_browser.py` / `item_browser.py` | mentionnés dans `SPEC.md`, non présents |
| `pal_image_list.py` | mentionné dans `SPEC.md`, non présent |
| `data/kits.dat` | mentionné dans `SPEC.md`, non présent |
| splash screen | mentionné dans `SPEC.md`, non observé |
| `Save As` toolbar | mentionné dans `SPEC.md`, non branché |
| affichage conditionnel proficiencies par classe | mentionné, non observé |

La spécification reste utile comme cible, mais elle doit être traitée comme un document d'intention, pas comme une description exacte de l'état actuel.

---

## 17. Différences fonctionnelles détaillées

### 17.1 Fonctionnalités présentes dans les deux

- Ouverture d'une sauvegarde `BALDUR.GAM`.
- Lecture des personnages embarqués.
- Édition des attributs principaux.
- Édition HP/AC/THAC0/XP/or/niveaux.
- Édition jets de sauvegarde et résistances.
- Édition des thief skills.
- Édition des couleurs, portraits et scripts.
- Gestion des sorts connus.
- Gestion des slots de mémorisation.
- Gestion des proficiencies.
- Lecture/écriture de l'inventaire au niveau modèle.
- Lecture de `dialog.tlk`.
- Recherche de chaîne TLK.
- Export `.CHR` au moins au niveau modèle/fonction.
- Chargement de ressources via KEY/BIF.
- Priorité aux ressources `override/`.
- Décodage BAM.

### 17.2 Fonctionnalités ou comportements Qt absents/incomplets en Python

- `Save As` avec création d'un nouveau dossier de sauvegarde.
- Renommage complet de sauvegarde via `SaveGameNameDialog`.
- Item browser graphique.
- Spell browser graphique.
- Creature browser.
- Éditeur de listes custom Kits/Affects.
- Éditeur d'affects génériques.
- Éditeur de variables globales.
- Éditeur de variables locales.
- Éditeur du journal.
- Onglet Appearance équivalent à l'ancien UI.
- Changement de portrait par navigateur.
- Gestion Black Pits explicite.
- Support Windows documenté.
- Toolbar historique.
- Menus View/Settings complets.
- Application effective des limites de sorts connus/mémorisés.
- Application de l'option grille.
- Politique d'overwrite CHR/CRE complète.
- Import `.CHR` dans le party ou remplacement d'un personnage.
- Utilisation visible des icônes de sorts/items.
- Palette images personnage.

### 17.3 Fonctionnalités Python plus avancées ou mieux structurées

- Tests automatisés.
- Architecture modulaire plus claire.
- Parsers plus faciles à valider indépendamment de l'UI.
- Auto-détection Steam Linux/macOS plus utile que le stub Qt.
- Encoding TLK plus souple.
- Gestion Python des ressources plus centralisée.
- Édition effective basique de l'inventaire, alors que l'ancien Qt était principalement lecture seule côté UI.
- Ajout/retrait de sorts connus plus directement utilisable.
- Packaging Python standard.

### 17.4 Bugs ou dettes de l'ancien Qt à ne pas reproduire

- Validation Linux du chemin d'installation inachevée.
- `FindInstallPath()` stubbée.
- Certains menus/actions déclarés sans implémentation.
- Navigateurs Item/Spell présents mais sans logique réelle.
- Inventaire affiché mais non édité en pratique.
- Onglets Appearance/Affects/Globals/Journal vides.
- Bug observé sur la vitesse : mauvaise ligne UI utilisée dans `SetSpeed()`.
- Boucle de mise à jour des sorts potentiellement incorrecte.
- Plusieurs settings persistants mais non appliqués.
- Logging fichier prévu mais largement désactivé.

---

## 18. Différences techniques par module

### 18.1 Application core

| eekeeper-qt | py-eekeeper | Différence |
|---|---|---|
| `EEKeeper` / variables globales | `EEKeeperApp` singleton | Python réduit les globals dispersés |
| chargement ressources dans fenêtre/app | `ResourceManager` + app | meilleure séparation Python |
| `QSettings` historique | `Config` | Python encapsule mieux |
| log custom | peu de logging observé | logging Python à enrichir |

### 18.2 Formats

| eekeeper-qt | py-eekeeper | État Python |
|---|---|---|
| `CInfKey` | `InfKey` | proche |
| `CInfBifFile` | `InfBifFile` | proche, tests présents |
| `CInfGame` | `InfGame` | proche, tests présents |
| `CInfCreature` | `InfCreature` | proche, beaucoup de logique récente |
| `CInfChr` | `InfChr` | proche |
| `CInfTlk` | `InfTlk` | proche |
| `CInf2DA` | `Inf2DA` | proche |
| `CInfBam` | `InfBam` | proche |
| `CValueList` | `ValueList` | format différent |
| `CSpellBitmaps` | `SpellBitmaps` | présent mais peu branché UI |
| `CPalImageList` | absent | manquant |

### 18.3 UI

| eekeeper-qt | py-eekeeper | État Python |
|---|---|---|
| `EEKeeperWindow` | `MainWindow` | plus simple |
| `SavedGameWidget` | `SavedGameWidget` | proche, NPC mieux signalés |
| `CharacterSheetWidget` | `CharacterSheetWidget` | proche sur champs principaux |
| `InventoryTab` | `InventoryTab` | Python plus éditable |
| `SpellTab` | `SpellTab` | Python plus éditable |
| `MemorizationTab` | `MemorizationTab` | proche |
| `ProficienciesTab` | `ProficienciesTab` | proche |
| `SpellBrowserWidget` | absent | manquant |
| `ItemBrowserWidget` | absent | manquant |
| `ValueListDialog` | présent mais orphelin | manquant côté menu |
| `SaveGameNameDialog` | présent mais orphelin | manquant côté menu |
| `InstallationDirectory` | `InstallationDialog` | Python plus pratique |

---

## 19. Matrice de parité fonctionnelle

| Fonctionnalité | Qt | Python | Verdict |
|---|---|---|---|
| Ouvrir save | Oui | Oui | Parité |
| Sauvegarder save | Oui | Oui | Parité |
| Save As | Oui | Non | Python en retard |
| Éditer stats principales | Oui | Oui | Parité |
| Éditer sorts connus | Partiel | Oui | Python mieux branché |
| Éditer mémorisation | Oui | Oui | Parité partielle |
| Éditer proficiencies | Oui | Oui | Parité |
| Éditer inventaire UI | Lecture seule | Basique | Python mieux |
| Éditer affects génériques | Non UI | Non UI | Égalité basse |
| Éditer globals/journal | Non UI | Non UI | Égalité basse |
| Export CHR | Partiel | Oui | Python mieux |
| Import CHR | Prévu | Parse seulement | Python incomplet |
| String finder | Oui | Oui | Parité |
| Item browser | Stub | Absent | Égalité basse |
| Spell browser | Stub | Absent | Égalité basse |
| Auto-detect install | Stub | Oui | Python mieux |
| Tests auto | Non | Oui | Python mieux |
| Windows | Oui | Non | Qt mieux |
| Black Pits saves | Oui | Incertain | Qt mieux |

---

## 20. Risques de non-parité binaire

Même si l'UI Python est déjà utilisable, les points suivants doivent être validés sur de vraies sauvegardes :

1. round-trip `BALDUR.GAM` sans altération du journal ;
2. round-trip CRE avec affects, proficiencies dual-class et vitesse ;
3. préservation des sorts mémorisés sans entrée known spell ;
4. ordre d'écriture priest/wizard/innate ;
5. comportement des items équipés et des quantités ;
6. priorité `override/` sur les ressources moddées ;
7. compatibilité BG:EE / BG2:EE / IWD:EE ;
8. import/export `.CHR` réellement intégré au party.

---

## 21. Recommandations de convergence

Pour atteindre une parité utile avec `eekeeper-qt`, sans recopier ses dettes, l'ordre recommandé serait :

1. **Brancher les dialogues déjà écrits** : `SaveGameNameDialog`, `ValueListDialog`.
2. **Compléter l'import CHR** dans le `GAM`.
3. **Ajouter un éditeur party/global** : or, réputation, globals.
4. **Créer les navigateurs Item/Spell** avec icônes BAM.
5. **Exposer les champs CRE avancés** : racial enemy, vitesse, flags, AC détaillée.
6. **Valider sur sauvegardes réelles** et ajouter des tests d'intégration avec fixtures de jeu.
7. **Corriger la documentation** (`README`, `SPEC`) pour refléter 38 slots, l'état réel des imports et l'absence de Windows.

---

## 22. Conclusion

`py-eekeeper` n'est pas une simple traduction ligne à ligne de `eekeeper-qt`. C'est une réécriture plus moderne, plus testable et plus maintenable, qui a déjà repris l'essentiel du moteur de formats et une grande partie de l'édition de personnage.

Par rapport à l'ancien Qt :

- **le moteur binaire est déjà proche ou supérieur sur la testabilité** ;
- **l'UI de base est plus cohérente sur l'édition effective de sorts et d'inventaire** ;
- **l'UI avancée, la gestion de sauvegarde étendue et plusieurs outils historiques manquent encore** ;
- **la documentation Python surestime parfois l'état réel du code**.

En pratique, `eekeeper-qt` reste une référence utile pour les comportements binaires subtils et les intentions historiques de l'éditeur, tandis que `py-eekeeper` est déjà un meilleur socle technique pour finir le produit, à condition de combler les écarts UI/flux listés dans ce rapport.

---

## 23. Sources analysées

- `/tmp/eekeeper-qt` — commit `41b612e`
- `/home/grm/dev/py-eekeeper/py_eekeeper/`
- `/home/grm/dev/py-eekeeper/tests/`
- `/home/grm/dev/py-eekeeper/README.md`
- `/home/grm/dev/py-eekeeper/SPEC.md`
- `/home/grm/dev/py-eekeeper/pyproject.toml`

Date du rapport : 5 juin 2026.

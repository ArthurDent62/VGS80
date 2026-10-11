"""
Dateiausgabe der Konfig-Dateien.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-03 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

import codecs
import shutil
from datetime import datetime

# Konstanten
_ORDNER_ZIEL = '../BAC2_Simulation/src/'
_ORDNER_ARCHIV = _ORDNER_ZIEL + 'Archiv/'
NAME_START = 'daten_'
NAME_EXT = '.py'
TXT_SPLIT = '# ' + '-'*76 + ' #'
TXT_ENDE = \
'# ------------------------------------------------------------- Ende Gelände #'
# globale Variable
kf = None       # aktuelle Konfig-Datei

# ----------------------------------------------------------------- Methoden #
def k_start(name, beschreib):
    """Beginnt eine neue Konfig-Datei zu schreiben.
    Jede Konfig muss hier gestartet werden, sonst wird in die letzte Datei
    geschrieben, oder ein Fehler geworfen.
    :param name      Name der neuen Konfig-Datei
    :param beschreib Kurzbeschreibung Inhalt
    """
    # Dateinamen prüfen, dann öffnen
    if not name.startswith(NAME_START):
        name = NAME_START + name
    if not name.endswith(NAME_EXT):
        name += NAME_EXT

    # sichern der vorherigen Version
    date_now = datetime.now()
    savename = f'{_ORDNER_ARCHIV}{date_now.strftime("%Y%m%d_%H%M_")}{name}'
    name = _ORDNER_ZIEL + name

    try:
        shutil.move(name, savename)
    except FileNotFoundError:
        pass        # dann ist halt nix zum sichern da

    # Kopfdaten schreiben
    global kf
    kf = codecs.open(name, 'w', 'utf-8')
    kf.write('"""\n')
    kf.write(beschreib + '\n')
    kf.write('"""\n')
    kf.write(TXT_SPLIT + '\n')
    kf.write(f'# (c) 2019-{date_now.strftime("%Y")} Walter Haschka\n')
    kf.write('#\n')
    kf.write(f'# {name}\n')
    kf.write('#\n')
    kf.write(f'# generiert nach Prüfung am {date_now.strftime("%Y-%m-%d")}' \
            + f' um {date_now.strftime("%H:%M:%S")}\n')
    kf.write(TXT_SPLIT + '\n')
    kf.write('# pylint: disable=bad-whitespace\n')
    kf.write('# Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht\n')
    kf.write('\n')

# -------------------------------------------------------------------------- #
INDENT = '    '
def k_zeile(zeile, inset, start_section=False):
    """Schreibt eine Zeile in die Konfig-Datei.
    :param zeile:   string mit dem zu schreibenden Inhalt, ohne führende Leerzeichen.
                    Ein Zeilenvorschub wird hinzugefügt.
    :param inset:   Ebene der Einrückung,
    :param start_section: wenn True, wird ein Text zur Sektionstrennung DAVOR eingefügt
    """
    global kf
    if start_section:
        kf.write(TXT_SPLIT + '\n')

    kf.write(f'{INDENT*inset}{zeile}\n')

# -------------------------------------------------------------------------- #
def k_ende():
    """Schließt die aktuelle Konfig-Datei. Jede Konfig muss hier geschlossen
    werden, andernfalls werden die Daten nicht gespeichert.
    """
    kf.write(TXT_ENDE + '\n')
    kf.close()

# ------------------------------------------------------------- Ende Gelände #

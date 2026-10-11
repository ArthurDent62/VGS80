"""
Prüfen der Daten für sonstige Tasten und Melder im Excel,
und Erstellung der Konfigurations-Datei für diese.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-01 wh Modul begonnen
# 0.1 2019-05-01 wh Umstellung xls nur Igel & Platz, Kanal wird berechnet
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

# from openpyxl import load_workbook

from m_common import TastenTyp
import m_daten
from m_tools import wsGet, col_nmbr

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace
# zwecks verbesserter Lesbarkeit

# Excel sheet
_SO = 'sonstigeMelderTasten'
_ROW_START = 3
_COL_MELD_TXT = col_nmbr('A')
_COL_BHF_KURZ = col_nmbr('B')
_COL_TAST_TXT = col_nmbr('C')
_COL_BESCHR   = col_nmbr('D')
_COL_TAST_CLR = col_nmbr('F')
_COL_MELD_DAT = col_nmbr('H')
_COL_TAST_DAT = col_nmbr('K')

# Modul-Variable
_ws = None       # Tabellenblatt

# pylint: enable=bad-whitespace
# ----------------------------------------------------------------- Methoden #
def _pruefe_melder(zeile):
    """Prüft und übernimmt die Daten eines Melders.
    :param zeile  Nummer der Zeile der Daten
    :return True  bei einem Fehler; sonst False
    """
    fehler = False

    # Daten holen
    b = wsGet(_ws, zeile, _COL_BESCHR)
    print(' :M='+b, end='', flush=True)

    b_lng = wsGet(_ws, zeile, _COL_MELD_TXT)
    bhf = wsGet(_ws, zeile, _COL_BHF_KURZ)
    bhf_txt = '' if bhf is None else f'{bhf}_'
    btx = f'{bhf_txt}{b}-Melder.'

    i = wsGet(_ws, zeile, _COL_MELD_DAT)
    p = wsGet(_ws, zeile, _COL_MELD_DAT +1)
    kanal_zahl = wsGet(_ws, zeile, _COL_MELD_DAT +2)

    # keine Anschlussdaten vorhanden - Info aber kein Fehler
    if i is None or p is None or kanal_zahl is None:
        print(f'\n  INFO! Melder {btx} ist nicht definiert!\n')
        return False

    # abgeleitete Daten rechnen
    kl, kr = m_daten.rechne_kanal(i, p)
    if kanal_zahl != 2:
        kr = None

    # melder merken
    if b in ('VGrM H', 'VGrM R'):
        m_daten.neu_spezi_melder(b, b_lng, kl, kr, bhf)
    else:
        m_daten.neu_melder(b, b_lng, kl, kr)

    # LED Kanäle belegen
    if kr is None:
        # Kanal rechts nicht gegeben, also einfacher Melder
        fehler |= m_daten.neu_1led(btx, i, p, kl)

    else:
        # Kanal rechts vorhanden, somit Doppel-LED-Melder
        fehler |= m_daten.neu_2leds(btx, 'links', 'rechts', i, p, kl, kr)

    return fehler

# -------------------------------------------------------------------------- #
def _pruefe_taste(zeile):
    """Prüft und übernimmt die Daten einer Taste.
    :param zeile  Nummer der Zeile der Daten
    :return True  bei einem Fehler; sonst False
    """
    fehler = False

    # Daten holen
    b = wsGet(_ws, zeile, _COL_BESCHR)

    print(' :T='+b, end='', flush=True)

    i = wsGet(_ws, zeile, _COL_TAST_DAT)
    p = wsGet(_ws, zeile, _COL_TAST_DAT +1)

    # keine Anschlussdaten vorhanden - Info aber kein Fehler
    if i is None or p is None:
        # Taste ist nicht definiert - Info aber kein Fehler
        print(f'\n  INFO! Taste {b} ist nicht definiert!\n')
        return False

    # abgeleitete Daten
    t = TastenTyp.GRUPPE
    if wsGet(_ws, zeile, _COL_TAST_CLR).lower() == 'weiß':
        t = TastenTyp.DOKU

    fehler |= m_daten.neu_taste(b, i, p, t, \
            wsGet(_ws, zeile, _COL_TAST_TXT))

    return fehler

# -------------------------------------------------------------------------- #
def pruefe(workbook):
    """Prüft das Tabellenblatt mit den Daten der sonstigen Tasten und Meldern.
    :param workbook Die bereits geöffnete Excel-Datei mit dem Blatt _SO.
    :return         True bei einem Fehler; sonst False
    """
    fehler = False
    empty = 0

    # Tabellenblatt vorhanden?
    if _SO not in workbook.sheetnames:
        print(f'\n  **** Tabellenblatt "{_SO}" fehlt ****')
        return True

    # prüfe Inhalt der _SO
    print('prüfe ' + _SO)

    global _ws
    _ws = workbook[_SO]
    wsRow = _ROW_START

    # solange Daten vorhanden sind - bis zu 5 Leerzeilen für Formatierung sind ok
    while empty < 5:

        if wsGet(_ws, wsRow, _COL_MELD_TXT) is not None:
            # hier wird ein Melder definiert
            empty = 0
            fehler |= _pruefe_melder(wsRow)

        elif wsGet(_ws, wsRow, _COL_TAST_TXT) is not None:
            # hier wird eine Taste definiert
            empty = 0
            fehler |= _pruefe_taste(wsRow)

        else:
            # leere Zeile - die zählen wir
            empty += 1
            print(f': ({wsRow})', end='', flush=True)

        wsRow = wsRow+1

    print('\n')
    return fehler

# ------------------------------------------------------------- Ende Gelände #

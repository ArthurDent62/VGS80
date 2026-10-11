"""
Lesen der Daten für die Steckigel und deren Verknüpfung mit den Platinen.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-04-29 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from m_daten import die_rahmen, neu_igel, neu_igel_platz, neu_tast_igel, IgelTyp
from m_tools import wsGet, col_nmbr

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace
# dient der übersichtlichen Formatierung

# Excel sheet
_TAB = 'Werte'
_ROW_START = 2
_COL_LED_NR   = col_nmbr('E')
_COL_LED_IGL  = col_nmbr('F')
_COL_SEQ      = col_nmbr('G')
_COL_TAST_ID  = col_nmbr('H')
_COL_TAST_IGL = col_nmbr('I')

# Info Rahmen
_ROW_RAHMEN1 = 10
_ROW_RAHMEN2 = 14
_COL_RAHMEN  = col_nmbr('P')
_TXT_USE = 'ja'

# defekte Plätze am Steckigel
_ROW_DEFECT_START = 30
_COL_DEFECT_IGL   = col_nmbr('F')
_COL_DEFECT_KNL   = col_nmbr('G')

# Defekt Text
_TXT_DEFECT = '---DEFEKT---'

# Modul-Variable
_ws = None       # Tabellenblatt

# pylint: enable=bad-whitespace
# ----------------------------------------------------------------- Methoden #
def pruefe(workbook):
    """Prüft das Tabellenblatt mit den Daten der Steckigel.
    :param workbook Die bereits geöffnete Excel-Datei mit dem Blatt _TAB.
    :return         True bei einem Fehler; sonst False
    """
    fehler = False

    # Tabellenblatt vorhanden?
    if _TAB not in workbook.sheetnames:
        print(f'\n  **** Tabellenblatt "{_TAB}" fehlt ****')
        return True

    # prüfe Inhalt des _TAB
    print('prüfe Daten der Igel in Blatt: ' + _TAB)

    global _ws
    _ws = workbook[_TAB]

    # prüfe welche Rahmen angeschalten werden sollen
    cell = wsGet(_ws, _ROW_RAHMEN1, _COL_RAHMEN)
    r1 = cell is not None and cell == _TXT_USE
    cell = wsGet(_ws, _ROW_RAHMEN2, _COL_RAHMEN)
    r2 = cell is not None and cell == _TXT_USE

    # ein Igel sollte schon Verwendung finden!
    fehler |= die_rahmen(r1, r2)

    # solange LED Igel definiert sind
    wsRow = _ROW_START
    while wsGet(_ws, wsRow, _COL_LED_NR) is not None:
        # LED Igel Daten
        anz_led = wsGet(_ws, wsRow, _COL_LED_NR)
        igel_name = wsGet(_ws, wsRow, _COL_LED_IGL)
        igel_seq = wsGet(_ws, wsRow, _COL_SEQ)
        print(f' . {igel_name}/{anz_led}', end='', flush=True)
        fehler |= neu_igel(igel_name, igel_seq, IgelTyp.find('LED', anz_led))

        # weiter zur nächsten Zeile
        wsRow = wsRow+1

    # solange Tasten-Igel definiert sind
    wsRow = _ROW_START
    while wsGet(_ws, wsRow, _COL_TAST_IGL) is not None:
        # Tasten Igel Daten
        igel_name = wsGet(_ws, wsRow, _COL_TAST_IGL)
        igel_seq = wsGet(_ws, wsRow, _COL_SEQ)
        igel_id = int(str(wsGet(_ws, wsRow, _COL_TAST_ID)), 16)
        print(f' . {igel_name}', end='', flush=True)
        fehler |= neu_tast_igel(igel_name, igel_seq, IgelTyp.TASTEN, igel_id)

        # weiter zur nächsten Zeile
        wsRow = wsRow+1

    # Igel-Zeile abschliessen
    print('\n\nDefekte Anschlüsse notiert:')

    # solange defekte Anschluesse definiert sind
    wsRow = _ROW_DEFECT_START
    while wsGet(_ws, wsRow, _COL_DEFECT_IGL) is not None:
        # LED Igel Daten
        igel_name = wsGet(_ws, wsRow, _COL_DEFECT_IGL)
        igel_knl = wsGet(_ws, wsRow, _COL_DEFECT_KNL)
        print(f' X {igel_name}/{igel_knl}', end='', flush=True)

        # ignoriere Fehler, denn der ganze Igel könnte ohne Verwendung sein
        neu_igel_platz(_TXT_DEFECT, igel_name, igel_knl, (_TXT_DEFECT,) *3)

        # weiter zur nächsten Zeile
        wsRow = wsRow+1

    print('\n')
    return fehler

# ------------------------------------------------------------- Ende Gelände #

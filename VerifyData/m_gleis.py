"""
Prüfen der Gleisabschnitts-Daten im Excel und Aufbereitung für die Erstellung der
Konfigurations-Datei.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-12-15 wh Modul begonnen
# -------------------------------------------------------------------------- #

import m_daten
from m_tools import wsGet, col_nmbr, col_ltr    # pylint: disable=unused-import

# ----------------------------------------------------- Konstante definieren #

# ----------------------------------------------------------------- Methoden #
def name_gleis(bahnhof, gleis_nummer):
    """Generiert den Namen/Bezeichnung des Gleisabschnitts aufgrund der gegebenen
    Parameter.
    :param bahnhof  Bahnhof wo sich der Gleisabschnitt befindet
    :param gleis_nummer Nummer des Abschnitts im Bahnhof
    :return string  Name des Gleisabschnitts
    """
    return f'G{gleis_nummer:0>3}_{bahnhof}'

# -------------------------------------------------------------------------- #
def _pruefe_blatt(workbook, bahnhof):
    """Prüft das Tabellenblatt mit den Daten der Weichen.
    :param workbook Die bereits geöffnete Excel-Datei mit dem Blatt _TAB.
    :param bahnhof  zu prüfender Bahnhof
    :return         True bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    # lokal konstant
    # pylint: disable=bad-whitespace

    # Excel sheet
    _TAB = 'Gleistabelle_'
    _TXT_HEAD_GROUP = 'Melder'
    _TXT_NEG = 'rot'
    _TXT_POS = 'fahr'
    _GLEIS_TYP = 'G'
    _ROW_HEAD_TOP = 1
    _ROW_START    = 4
    _COL_TYP    = col_nmbr('E')
    _COL_NAME   = col_nmbr('F')
    _COL_IGEL   = col_nmbr('K')
    _ANZ_COL    = 2

    # pylint: enable=bad-whitespace
    # kein Vorteil wenn die Prüfmethode aufgeteilt wird
    fehler = False

    # Tabellenblatt vorhanden?
    sheet_name = f'{_TAB}{bahnhof}'
    if sheet_name not in workbook.sheetnames:
        print(f'\n  **** Tabellenblatt "{sheet_name}" fehlt ****')
        return True

    # prüfe Inhalt der Blätter
    print('prüfe ' + sheet_name, end='')
    ws = workbook[sheet_name]   # Tabellenblatt

    # wie viele Melder-Spalten gibt es?
    groups = 0
    while True:
        inhalt = wsGet(ws, _ROW_HEAD_TOP, _COL_IGEL + groups * _ANZ_COL)
        if inhalt is None or inhalt[0:len(_TXT_HEAD_GROUP)] != _TXT_HEAD_GROUP:
            break       # keine weiteren Spaltengruppen

        groups += 1
#    print(f'  -  groups is {groups}!')

    # solange Abschnitte definiert sind
    wsRow = _ROW_START-1
    while True:
        # weiter zur nächsten Zeile (am Anfang, wegen dem continue)
        wsRow = wsRow+1

        g_typ = wsGet(ws, wsRow, _COL_TYP)
        if g_typ is None:
            break
        if g_typ != _GLEIS_TYP:
            continue

        # da ist also noch ein Abschnitt
        g_name = wsGet(ws, wsRow, _COL_NAME)
        print(f'  {g_name}', end='')
        glbe = name_gleis(bahnhof, g_name)
        kanal_pos = set()
        kanal_neg = set()

        # LED und Igel prüfen
        for group in range(groups):
            wsCol = _COL_IGEL + group*_ANZ_COL
            akt_igel = wsGet(ws, wsRow, wsCol + 0)
            if akt_igel is None:    # keine (weiteren) Daten, überspringen
                continue

            akt_platz = wsGet(ws, wsRow, wsCol + 1)
            led_kan_pos, led_kan_neg = m_daten.rechne_kanal(akt_igel, akt_platz)

#            print(f'\nZelle: {col_ltr(wsCol)}{wsRow} ** igel={akt_igel} ** ' \
#                  + f'platz={akt_platz} ** kanal={led_kan_pos}')
            kanal_pos.add(led_kan_pos)
            kanal_neg.add(led_kan_neg)

            fehler |= m_daten.neu_2leds(glbe + f'/{group}: ', _TXT_POS, _TXT_NEG, \
                        akt_igel, akt_platz, led_kan_pos, led_kan_neg)

        # prüfen ob LEDs für den Abschnitt gefunden wurden
        if not kanal_neg or not kanal_pos:
            print(f'\n ** positive LED={kanal_pos}, negative={kanal_neg} ' + \
                  'sollten beide befüllt sein!')
            fehler = True
            continue    # keine LEDs? stopp!

        # Gleisabschnitt zu den Daten hinzufügen
        fehler |= m_daten.neu_gleis(glbe, kanal_pos, kanal_neg)

    if fehler:
        print(' :-(  Fehler vorhanden!')
    else:
        print(' ... ok')
        # print(f'Gleistabelle = {m_daten.gleis}')    # DEBUG
    return fehler

# -------------------------------------------------------------------------- #
def pruefe(workbook):
    """Prüft die Tabellenblätter mit den Daten der Gleisabschnitte.
    :param workbook Die bereits geöffnete Excel-Datei.
    :return         True bei einem Fehler; sonst False
    """
    fehler = False

    print(f'\nGleisabschnittprüfung - folgende Bahnhöfe gefunden: {m_daten.bahnhofset()}')
    for b in m_daten.bahnhofset():
        fehler |= _pruefe_blatt(workbook, b)

    return fehler

# ------------------------------------------------------------- Ende Gelände #

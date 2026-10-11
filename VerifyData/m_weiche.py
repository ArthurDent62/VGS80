"""
Prüfen der Weichen-Daten im Excel und Aufbereitung für die Erstellung der
Konfigurations-Datei.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-01 wh Modul begonnen
# 0.1 2019-04-30 wh Umstellung xls nur Igel & Platz, Kanal wird berechnet
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from m_common import TastenTyp
import m_daten
from m_tools import wsGet, col_nmbr

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace

# Excel sheet
_TAB = 'Weichentabelle'
_ROW_START = 3
_COL_BF    = col_nmbr('A')
_COL_BEZ   = col_nmbr('B')
_COL_INIT  = col_nmbr('D')
_COL_ORTS  = col_nmbr('F')
_COL_START = col_nmbr('G')
_COL_TASTE = col_nmbr('M')

# Modul-Variable
_ws = None       # Tabellenblatt

# pylint: enable=bad-whitespace
# ----------------------------------------------------------------- Methoden #
def name_der_weichentaste(bahnhof, weichen_nummer):
    """Generiert den Namen/Bezeichnung der Weichentaste aufgrund der gegebenen
    Parameter.
    :param bahnhof  Bahnhof wo die Weiche verbaut ist
    :param weichen_nummer Nummer der Weiche im Bahnhof
    :return string  Name der Taste
    """
    return f'WT_{bahnhof}_{weichen_nummer:0>3}'

# -------------------------------------------------------------------------- #
def pruefe(workbook):
    """Prüft das Tabellenblatt mit den Daten der Weichen.
    :param workbook Die bereits geöffnete Excel-Datei mit dem Blatt _TAB.
    :return         True bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-locals
    # kein Vorteil wenn die Prüfmethode aufgeteilt wird
    fehler = False

    # Tabellenblatt vorhanden?
    if _TAB not in workbook.sheetnames:
        print(f'\n  **** Tabellenblatt "{_TAB}" fehlt ****')
        return True

    # prüfe Inhalt der _TAB
    print('prüfe ' + _TAB, end='', flush=True)

    global _ws
    _ws = workbook[_TAB]
    wsRow = _ROW_START
    bf_bisher = 'fehlt'

    # solange Weichen definiert sind
    while wsGet(_ws, wsRow, _COL_BF) is not None:
        bf_aktuell = wsGet(_ws, wsRow, _COL_BF)
        if bf_aktuell != bf_bisher:
            print(f'\nin {bf_aktuell:4}', end='', flush=True)   # Abschluss vorige Zeile
            bf_bisher = bf_aktuell

        print(f' :{wsGet(_ws, wsRow, _COL_BEZ):3}', end='', flush=True)

        wnum = wsGet(_ws, wsRow, _COL_BEZ)

        # Weiche fernbedient oder ortsbedient (Sperrschuh, Schutzweiche)
        w_ort = wsGet(_ws, wsRow, _COL_ORTS)
        w_is_fern = w_ort is None or len(w_ort.strip()) < 2
        webe = 'FernW' if w_is_fern else 'OrtsW'
        webe += f' {bf_aktuell}:{wnum:3}'
        txt_re = webe + (' : rechts:' if w_is_fern else ' : ')

        # LED und Igel prüfen
        akt_igel = wsGet(_ws, wsRow, _COL_START + 0)
        akt_platz = wsGet(_ws, wsRow, _COL_START + 1)
        ledKanVer, ledKanSperr = m_daten.rechne_kanal(akt_igel, akt_platz)
        fehler |= m_daten.neu_2leds(webe + ' : ', 'verschluss', 'gesperrt', \
                akt_igel, akt_platz, ledKanVer, ledKanSperr)

        akt_igel = wsGet(_ws, wsRow, _COL_START + 2)
        akt_platz = wsGet(_ws, wsRow, _COL_START + 3)
        ledKanReFrei, ledKanReBel = m_daten.rechne_kanal(akt_igel, akt_platz)
        fehler |= m_daten.neu_2leds(txt_re, 'weiß', 'rot', \
                akt_igel, akt_platz, ledKanReFrei, ledKanReBel)

        akt_igel = wsGet(_ws, wsRow, _COL_START + 4)
        akt_platz = wsGet(_ws, wsRow, _COL_START + 5)
        ledKanLiFrei, ledKanLiBel = m_daten.rechne_kanal(akt_igel, akt_platz)

        led_list = [ledKanVer, ledKanSperr, ledKanReFrei, ledKanReBel, ledKanLiFrei]

        if w_is_fern:
            # fernbedient: linker Abzweig mit zwei LED
            fehler |= m_daten.neu_2leds(webe + ' : links:', 'weiß', 'rot', \
                    akt_igel, akt_platz, ledKanLiFrei, ledKanLiBel)
            led_list.append(ledKanLiBel)
        else:
            # ortsbedient: Sperrschuh / Schutzweiche mit nur einer LED
            fehler |= m_daten.neu_1led(webe + ' : Sperr/Schutzw', \
                    akt_igel, akt_platz, ledKanLiFrei)

        # Taste und Igel prüfen
        wtas = name_der_weichentaste(bf_aktuell, wnum)
        akt_igel = wsGet(_ws, wsRow, _COL_TASTE)
        akt_platz = wsGet(_ws, wsRow, _COL_TASTE + 1)
        fehler |= m_daten.neu_taste(wtas, akt_igel, akt_platz, \
                TastenTyp.WEICHE, 'Taste ' + webe)

        # Weichendaten merken
        v_links = wsGet(_ws, wsRow, _COL_INIT)
        v_rechts = wsGet(_ws, wsRow, _COL_INIT+1)
        b_init_links = str(v_links).lower() == 'u' or \
                (str(v_rechts).lower() != 'u' and v_links > v_rechts)
        fehler |= m_daten.neu_weiche(wtas, 'f' if w_is_fern else 'o', \
                                     bf_aktuell, b_init_links, led_list)

        # weiter zur nächsten
        wsRow = wsRow+1

    print('\n')
    return fehler

# ------------------------------------------------------------- Ende Gelände #

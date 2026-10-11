"""
Prüfen der Signal-Daten im Excel und Aufbereitung für die Erstellung der
Konfigurations-Datei.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-03-02 wh Modul begonnen
# 0.1 2019-04-30 wh Umstellung xls nur Igel & Platz, Kanal wird berechnet
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from m_common import TastenTyp
import m_daten
from m_tools import wsGet, col_ltr, col_nmbr

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace
# Excel sheet
_TAB = 'Signaltabelle'
_ROW_START = 3
_COL_BHF    = col_nmbr('A')
_COL_TYP    = col_nmbr('B')
_COL_NAM_HS = col_nmbr('C')
_COL_NAM_SO = col_nmbr('D')
_COL_HS_GESCHW = col_nmbr('F')
_COL_VS_GESCHW = col_nmbr('I')
_COL_HS_GRUEN  = col_nmbr('L')
_COL_HS_ROT    = col_nmbr('N')
_COL_HS_WEISS  = col_nmbr('P')
_COL_VS_ORANG  = col_nmbr('R')
_COL_VS_GRUEN  = col_nmbr('T')
_COL_VERS_VER  = col_nmbr('V')
_COL_VERS_AUF  = col_nmbr('X')
_COL_FAHRSTRA  = col_nmbr('Z')
_COL_SPERR     = col_nmbr('AB')
_COL_TASTE     = col_nmbr('AD')
_COL_TAST_LANG = col_nmbr('AF')

# Modul-Variable
_ws = None       # Tabellenblatt

# pylint: enable=bad-whitespace
# ----------------------------------------------------------------- Methoden #
def _myf(an_object):
    """Formatiere ein als None definiertes Objekt als Leerstring (statt "None")
    """
    return "" if an_object is None else an_object

# -------------------------------------------------------------------------- #
def _leer_pruefung(row, funk, spalten_block):
    """Prüfe die gegebenen Spalten samt der nächsten auf Inhaltslosigkeit.
    :param row           int    aktuelle Zeile
    :param funk          str    für Fehlermeldung - welche Funktionsprüfung?
    :param spalten_block (int)  Liste von Spalten-Nummern
    :returns             bool   True bei Fehler
    """
    fehler = False

    for spa in spalten_block:
        for i in range(2):
            if wsGet(_ws, row, spa+i):
                print(f'\n  ** Fehler {funk}: Spalte {col_ltr(spa+i)} nicht leer!')
                fehler = True

    return fehler

# -------------------------------------------------------------------------- #
def _pruefe_led_kombi(beschreib, led0, led1):
    """Prüfen und kombinieren zweier LEDs auf einen Steckplatz.
    Wegen der möglichen Kombinationen der Signalanzeigen wird jede LED
    im Daten-XLSX einzeln eingetragen, auch wenn diese gemeinsam mit einer
    anderen LED am gleichen Stecker hängt. Hier wird das konsolidert.
    :param beschreib str    Basis-Beschreibung
    :param led0    (tupel) = (igel, platz, kanal, beschreib)
    :param led1    (tupel)
    :returns         bool   True bei einem Fehler
    """
    fehler = False
    if led0[0] != led1[0]:     # Igel
        print(f'\n  ** Igel für {beschreib}: {led0[3]}:{led0[0]} <> {led1[3]}:{led1[0]}')
        fehler = True
    if led0[1] != led1[1]:     # Steckplatz
        print(f'\n  ** Steckplatz für {beschreib}: {led0[3]}:{led0[1]} <> {led1[3]}:{led1[1]}')
        fehler = True

    fehler |= m_daten.neu_2leds(beschreib, led0[3], led1[3], \
                                    led0[0], led0[1], led0[2], led1[2])
    return fehler

# -------------------------------------------------------------------------- #
def name_der_signaltaste(bhf, signal_name, lang=None):
    """Liefert den Namen der Signaltaste für die gegebenen Parameter.
    :param bhf         str   Betriebsstelle (Kürzel)
    :param signal_name str   bei kombinierten Signalen nur das Hauptsignal
    :param lang        bool  True=lange, False=kurze Einfahrt, None=gibt nur eine
    :returns           str   Name der Signaltaste
    """
    ext = ''
    if lang is not None:
        ext = '_lng' if lang else '_krz'

    return f'ST_{bhf}_{signal_name}{ext}'

# -------------------------------------------------------------------------- #
def _pruef_evs(typ, row, bhf, name_hs, name_so):
    """Prüft die Angaben für ein Einfahr-Vorsignal.
    :param typ       str    Signaltyp
    :param row       int    aktuelle Zeile
    :param bhf       str    Betriebsstelle (Kürzel)
    :param name_hs   str    Name für Hauptsignal (zur Prüfung)
    :param name_so   str    Name des Signals
    :returns         bool   True bei einem Fehler
    """
    fehler = False

    if name_hs:
        # bei Hauptsignal darf da kein Name stehen
        print(f'\n  ** Fehler {typ}: Name Hauptsignal vorhanden!')
        fehler = True
    if not name_so:
        # Name Vorsignal muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name vorhanden!')
        fehler = True

    # prüfe weitere Felder die leer sein müssen
    fehler |= _leer_pruefung(row, typ, \
                (_COL_HS_GESCHW, _COL_HS_GRUEN, _COL_HS_ROT, _COL_HS_WEISS, \
                _COL_VERS_VER, _COL_VERS_AUF, _COL_FAHRSTRA, _COL_TAST_LANG))

    # prüfe die Angaben
    beschreib = f'{bhf}_{name_so}'
    sig_name = name_der_signaltaste(bhf, name_so)

    # LEDs
    akt_igel = wsGet(_ws, row, _COL_VS_ORANG)
    akt_platz = wsGet(_ws, row, _COL_VS_ORANG + 1)
    led_orange, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + ' -VORSICHT-', \
                                   akt_igel, akt_platz, led_orange)

    akt_igel = wsGet(_ws, row, _COL_VS_GRUEN)
    akt_platz = wsGet(_ws, row, _COL_VS_GRUEN + 1)
    led_vs_gruen, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + ' -HS FREI-', \
                                akt_igel, akt_platz, led_vs_gruen)

    akt_igel = wsGet(_ws, row, _COL_SPERR)
    akt_platz = wsGet(_ws, row, _COL_SPERR + 1)
    led_sperr, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_SperrM', akt_igel, akt_platz, \
                                   led_sperr)

    # Taste
    akt_igel = wsGet(_ws, row, _COL_TASTE)
    akt_platz = wsGet(_ws, row, _COL_TASTE + 1)
    fehler |= m_daten.neu_taste(sig_name, akt_igel, akt_platz, TastenTyp.VORSIG, \
                                   f'Einfahr-Vorsignal {name_so} für {bhf}')

    # Programmdaten übergeben
    fehler |= m_daten.neu_signal(sig_name, typ, bhf, name_so, \
                (led_orange, led_vs_gruen, led_sperr))

    # Vorsignal merken für Verbindung zum Hauptsignal
    m_daten.neu_vorsignal(bhf, name_so, sig_name)
    return fehler

# -------------------------------------------------------------------------- #
def _pruef_ausfahrt(typ, row, bhf, name_hs, name_so):
    """Prüft die Angaben für ein "Signal" Ausfahrt. Dieses entspricht keinem
    Signal in der Realität, sondern der Streckentaste am VGS80.
    :param typ       str    Signaltyp
    :param row       int    aktuelle Zeile
    :param bhf       str    Betriebsstelle (Kürzel)
    :param name_hs   str    Name für Hauptsignal (zur Prüfung)
    :param name_so   str    Name des "Signals"
    :returns         bool   True bei einem Fehler
    """
    fehler = False

    if name_hs:
        # bei Hauptsignal darf da kein Name stehen
        print(f'\n  ** Fehler {typ}: Name Hauptsignal vorhanden!')
        fehler = True
    if not name_so:
        # Name der Ausfahrt muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name vorhanden!')
        fehler = True

    # prüfe weitere Felder die leer sein müssen
    fehler |= _leer_pruefung(row, typ, \
                (_COL_HS_GESCHW, _COL_HS_GRUEN, _COL_HS_ROT, _COL_HS_WEISS, \
                _COL_VS_GESCHW, _COL_VS_GRUEN, _COL_VS_ORANG, \
                _COL_VERS_VER, _COL_VERS_AUF, _COL_TAST_LANG))

    # prüfe die Angaben
    beschreib = f'{bhf}_{name_so}'
    sig_name = name_der_signaltaste(bhf, name_so)

    # LEDs
    akt_igel = wsGet(_ws, row, _COL_FAHRSTRA)
    akt_platz = wsGet(_ws, row, _COL_FAHRSTRA + 1)
    led_speicher, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_SpeicherM', \
                                   akt_igel, akt_platz, led_speicher)

    akt_igel = wsGet(_ws, row, _COL_SPERR)
    akt_platz = wsGet(_ws, row, _COL_SPERR + 1)
    led_sperr, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_SperrM', akt_igel, akt_platz, led_sperr)

    # Taste
    akt_igel = wsGet(_ws, row, _COL_TASTE)
    akt_platz = wsGet(_ws, row, _COL_TASTE + 1)
    fehler |= m_daten.neu_taste(sig_name, akt_igel, akt_platz, TastenTyp.STRECKE, \
                                   f'von {bhf} auf Strecke {name_so}')

    # Ausfahrt: Programmdaten übergeben
    fehler |= m_daten.neu_signal(sig_name, typ, bhf, name_so, \
                (led_speicher, led_sperr))

    return fehler

# -------------------------------------------------------------------------- #
def _pruef_es_avs(typ, row, bhf, name_hs, name_so):
    """Prüft die Angaben für ein Einfahrsignal mit Ausfahr-Vorsignal.
    :param typ       str    Signaltyp
    :param row       int    aktuelle Zeile
    :param bhf       str    Betriebsstelle (Kürzel)
    :param name_hs   str    Name für Hauptsignal
    :param name_so   str    Name des Signals
    :returns         bool   True bei einem Fehler
    """
    # pylint: disable=too-many-locals
    # Vermeidung Mehrfachzugriff durch mehr Variablen

    fehler = False

    if not name_hs:
        # Name Hauptsignal muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name Hauptsignal vorhanden!')
        fehler = True
    if not name_so:
        # Name Vorsignal muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name Vorsignal vorhanden!')
        fehler = True

    # prüfe weitere Felder die leer sein müssen
    fehler |= _leer_pruefung(row, typ, \
                (_COL_VERS_VER, _COL_VERS_AUF, _COL_SPERR, _COL_TAST_LANG))

    # prüfe die Angaben
    beschreib = f'{bhf}_{name_hs}_{name_so}'
    sig_name = name_der_signaltaste(bhf, name_hs)

    # LEDs
    akt_igel = wsGet(_ws, row, _COL_HS_GRUEN)
    akt_platz = wsGet(_ws, row, _COL_HS_GRUEN + 1)
    rot_igel = wsGet(_ws, row, _COL_HS_ROT)
    rot_platz = wsGet(_ws, row, _COL_HS_ROT + 1)
    led_hs_gruen, led_hs_rot = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= _pruefe_led_kombi(beschreib + ' ', \
                                (akt_igel, akt_platz, led_hs_gruen, '-FREI-'), \
                                (rot_igel, rot_platz, led_hs_rot, '-HALT-'))

    akt_igel = wsGet(_ws, row, _COL_HS_WEISS)
    akt_platz = wsGet(_ws, row, _COL_HS_WEISS + 1)
    vs_igel = wsGet(_ws, row, _COL_VS_ORANG)
    vs_platz = wsGet(_ws, row, _COL_VS_ORANG + 1)
    led_hs_weiss, led_vs_orang = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= _pruefe_led_kombi(beschreib + ' ', \
                                (akt_igel, akt_platz, led_hs_weiss, '-ERSATZ-'), \
                                (vs_igel, vs_platz, led_vs_orang, '-VORSICHT-'))

    akt_igel = wsGet(_ws, row, _COL_VS_GRUEN)
    akt_platz = wsGet(_ws, row, _COL_VS_GRUEN + 1)
    led_vs_gruen, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + ' -HS FREI-', \
                                akt_igel, akt_platz, led_vs_gruen)

    akt_igel = wsGet(_ws, row, _COL_FAHRSTRA)
    akt_platz = wsGet(_ws, row, _COL_FAHRSTRA + 1)
    led_fahrstra, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_Fahrstraße', \
                                   akt_igel, akt_platz, led_fahrstra)

    # Taste
    akt_igel = wsGet(_ws, row, _COL_TASTE)
    akt_platz = wsGet(_ws, row, _COL_TASTE + 1)
    fehler |= m_daten.neu_taste(sig_name, akt_igel, akt_platz, TastenTyp.ES, \
                                   f'Einfahrt in {bhf} {name_hs}+{name_so}')

    fehler |= m_daten.neu_signal(sig_name, typ, bhf, name_hs, \
                (led_hs_gruen, led_hs_rot, led_hs_weiss, \
                 led_vs_orang, led_vs_gruen, led_fahrstra))

    # Vorsignal merken für Verbindung zum Hauptsignal
    # durch geänderte Vorsignal-Logik der Simulation muss sich AVS nicht mehr registrieren
#     m_daten.neu_vorsignal(bhf, name_so, sig_name)
    return fehler

# -------------------------------------------------------------------------- #
def _pruef_as_vers(typ, row, bhf, name_hs, name_so):
    """Prüft die Angaben für ein Einfahrsignal mit Ausfahr-Vorsignal.
    :param typ       str    Signaltyp
    :param row       int    aktuelle Zeile
    :param bhf       str    Betriebsstelle (Kürzel)
    :param name_hs   str    Name für Hauptsignal
    :param name_so   str    Name des Signals
    :returns         bool   True bei einem Fehler
    """
    # pylint: disable=too-many-locals
    # Vermeidung Mehrfachzugriff durch mehr Variablen

    fehler = False

    if not name_hs:
        # Name Hauptsignal muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name Hauptsignal vorhanden!')
        fehler = True
    if name_so:
        # kein sonstiger Name darf vorhanden sein
        print(f'\n  ** Fehler {typ}: sonstiger Name vorhanden!')
        fehler = True

    # prüfe weitere Felder die leer sein müssen
    fehler |= _leer_pruefung(row, typ, \
                (_COL_VS_GESCHW, _COL_VS_GRUEN, _COL_VS_ORANG, _COL_VERS_VER))

    # Vorbereitung der Daten
    beschreib = f'{bhf}_{name_hs}'
    hat_lang = wsGet(_ws, row, _COL_TAST_LANG + 1) is not None
    sig_kurz = name_der_signaltaste(bhf, name_hs, False if hat_lang else None)
    sig_lang = name_der_signaltaste(bhf, name_hs, True)

    # LEDs
    akt_igel = wsGet(_ws, row, _COL_HS_GRUEN)
    akt_platz = wsGet(_ws, row, _COL_HS_GRUEN + 1)
    led_hs_gruen, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + ' -FREI-', \
                                   akt_igel, akt_platz, led_hs_gruen)

    ers_igel = wsGet(_ws, row, _COL_HS_WEISS)
    ers_platz = wsGet(_ws, row, _COL_HS_WEISS + 1)
    akt_igel = wsGet(_ws, row, _COL_HS_ROT)
    akt_platz = wsGet(_ws, row, _COL_HS_ROT + 1)
    led_hs_weiss, led_hs_rot = m_daten.rechne_kanal(ers_igel, ers_platz)
    fehler |= _pruefe_led_kombi(beschreib + ' ', \
                                (ers_igel, ers_platz, led_hs_weiss, '-ERSATZ-'), \
                                (akt_igel, akt_platz, led_hs_rot, '-HALT-'))

    akt_igel = wsGet(_ws, row, _COL_VERS_AUF)
    akt_platz = wsGet(_ws, row, _COL_VERS_AUF + 1)
    led_vers_auf, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + ' -VER.AUF.-', \
                                   akt_igel, akt_platz, led_vers_auf)

    akt_igel = wsGet(_ws, row, _COL_FAHRSTRA)
    akt_platz = wsGet(_ws, row, _COL_FAHRSTRA + 1)
    led_fahrstra, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_Fahrstraße', \
                                   akt_igel, akt_platz, led_fahrstra)

    akt_igel = wsGet(_ws, row, _COL_SPERR)
    akt_platz = wsGet(_ws, row, _COL_SPERR + 1)
    led_sperr, _ = m_daten.rechne_kanal(akt_igel, akt_platz)
    fehler |= m_daten.neu_1led(beschreib + '_SperrM', akt_igel, akt_platz, led_sperr)

    # Taste
    akt_igel = wsGet(_ws, row, _COL_TASTE)
    akt_platz = wsGet(_ws, row, _COL_TASTE + 1)
    fehler |= m_daten.neu_taste(sig_kurz, akt_igel, akt_platz, TastenTyp.AS, \
                                   f'AusfahrtSignal in {bhf} {name_hs} kurz')

    fehler |= m_daten.neu_signal(sig_kurz, typ, bhf, name_hs, \
                (led_hs_gruen, led_hs_weiss, led_hs_rot, \
                 led_vers_auf, led_fahrstra, led_sperr))

    # AS lang vorhanden - Programmdaten übergeben
    if hat_lang:
        akt_igel = wsGet(_ws, row, _COL_TAST_LANG)
        akt_platz = wsGet(_ws, row, _COL_TAST_LANG + 1)
        fehler |= m_daten.neu_taste(sig_lang, akt_igel, akt_platz, TastenTyp.AS_LANG, \
                                   f'AusfahrtSignal in {bhf} {name_hs} lang')

        fehler |= m_daten.neu_as_lang(sig_lang, sig_kurz)

    return fehler

# -------------------------------------------------------------------------- #
def _pruef_vers(typ, row, bhf, name_hs, name_so):
    """Prüft die Angaben für ein Verschubsignal.
    :param typ       str    Signaltyp
    :param row       int    aktuelle Zeile
    :param bhf       str    Betriebsstelle (Kürzel)
    :param name_hs   str    Name für Hauptsignal
    :param name_so   str    Name des Signals
    :returns         bool   True bei einem Fehler
    """
    fehler = False

    if name_hs:
        # bei Hauptsignal darf da kein Name stehen
        print(f'\n  ** Fehler {typ}: Name Hauptsignal vorhanden!')
        fehler = True
    if not name_so:
        # Name Verschubsignal muss vorhanden sein
        print(f'\n  ** Fehler {typ}: kein Name Verschubsignal vorhanden!')
        fehler = True

    # prüfe weitere Felder die leer sein müssen
    fehler |= _leer_pruefung(row, typ, \
                (_COL_HS_GESCHW, _COL_HS_GRUEN, _COL_HS_ROT, _COL_HS_WEISS, \
                 _COL_VS_GESCHW, _COL_VS_GRUEN, _COL_VS_ORANG, \
                 _COL_FAHRSTRA, _COL_SPERR, _COL_TAST_LANG))

    # prüfe die Angaben
    beschreib = f'{bhf}_{name_so}'
    sig_name = name_der_signaltaste(bhf, name_so)

    # LEDs
    akt_igel = wsGet(_ws, row, _COL_VERS_VER)
    akt_platz = wsGet(_ws, row, _COL_VERS_VER + 1)
    auf_igel = wsGet(_ws, row, _COL_VERS_AUF)
    auf_platz = wsGet(_ws, row, _COL_VERS_AUF + 1)

    led_vers_ver, led_vers_auf = m_daten.rechne_kanal(akt_igel, akt_platz)

    fehler |= _pruefe_led_kombi(beschreib + ' ', \
                            (akt_igel, akt_platz, led_vers_ver, '-VER.VERBOT-'), \
                            (auf_igel, auf_platz, led_vers_auf, '-VER.AUF.-'))

    # Taste
    akt_igel = wsGet(_ws, row, _COL_TASTE)
    akt_platz = wsGet(_ws, row, _COL_TASTE + 1)
    fehler |= m_daten.neu_taste(sig_name, akt_igel, akt_platz, TastenTyp.VERSCHUB, \
                                   f'{bhf} - Verschubsignal {name_so}')

    # Programmdaten übergeben
    fehler |= m_daten.neu_signal(sig_name, typ, bhf, name_so, \
                (led_vers_ver, led_vers_auf))

    return fehler

# -------------------------------------------------------------------------- #
# globales Nachschlagewerk wegen Interpreter erst hier

_pruefer = {'Ausfahrt' : _pruef_ausfahrt, \
            'EVS' : _pruef_evs, \
            'ES+AVS' : _pruef_es_avs, \
            'AS+VerS' : _pruef_as_vers, \
            'VerS' : _pruef_vers}

# -------------------------------------------------------------------------- #
def pruefe(workbook):
    """Prüft das Tabellenblatt mit den Daten der Signale.
    :param workbook Die bereits geöffnete Excel-Datei mit dem Blatt _TAB.
    :return         True bei einem Fehler; sonst False
    """
    fehler = False

    # Tabellenblatt vorhanden?
    if _TAB not in workbook.sheetnames:
        print(f'\n  **** Tabellenblatt "{_TAB}" fehlt ****')
        return True

    # prüfe Inhalt der _TAB
    print('prüfe ' + _TAB)

    global _ws
    _ws = workbook[_TAB]
    wsRow = _ROW_START

    while True:
        # solange Signale definiert sind
        s_typ = wsGet(_ws, wsRow, _COL_TYP)
        if not s_typ:
            break

        # weitere Basisdaten holen
        bhf = wsGet(_ws, wsRow, _COL_BHF)
        name_hs = wsGet(_ws, wsRow, _COL_NAM_HS)
        name_so = wsGet(_ws, wsRow, _COL_NAM_SO)
        print(f'\t{bhf}:{_myf(name_hs)}{_myf(name_so)}', end='', flush=True)

        # Prüfung entsprechend dem Signaltyp verzweigen
        try:
            fehler |= _pruefer[s_typ](s_typ, wsRow, bhf, name_hs, name_so)
        except KeyError:
            # unbekannter Signaltyp
            print(f'\n  ** unbekannter Signaltyp:{s_typ}!')
            fehler = True

        # weiter zum nächsten
        wsRow = wsRow+1

    print('')
    return fehler

# ------------------------------------------------------------- Ende Gelände #

"""
Prüfen der Fahrstrassen-Daten im Excel und Aufbereitung für die Erstellung der
Konfigurations-Datei.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-04-12 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

import m_daten
from m_tools import wsGet, col_ltr, col_nmbr, merged_cell_last_col as last_col
from m_gleis import name_gleis
from m_signal import name_der_signaltaste
from m_weiche import name_der_weichentaste

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace
# Excel sheet
_TAB = 'Sperrenplan_'
_ROW_KATEGORIE = 1
_ROW_BEZEICH   = 2
_ROW_DETAIL    = 3
_ROW_START     = 4
COL_STRECKE  = col_nmbr('A')
COL_GLEIS    = col_nmbr('B')
COL_FS_START = col_nmbr('C')
COL_FS_ZIEL_OHNE = col_nmbr('D')
COL_FS_ZIEL_MIT  = col_nmbr('E')
COL_FERN     = col_nmbr('F')

# Konstanten
_IST_EGAL = 'x'
_W_LINKS  = 'L'
_W_RECHTS = 'R'
_FS_AUS   = chr(8212)   # 'langer Bindestrich'
# _FS_D     = 'D'         # derzeit unbekannte Bedeutung (Durchfahrt?)
_FS_OK    = 'o'         # Fahrstrasse behindert nicht
_FS_SELBST= chr(8226)   # 'fetter Punkt'

# pylint: enable=bad-whitespace
# ----------------------------------------------------------------- Methoden #
def id_fs(start_taste, ziel_taste):
    """Generiert den Bezeichner einer Fahrstrasse aus Name der Taste für
    Startsignal und Zielsignal.
    :param start_taste  str  Name der Taste des Startsignals (das was frei wird)
    :param ziel_taste   str  Name der Taste des Fahrstrassenziels
    :return string  Bezeichner der Fahrstrasse
    """
    return (start_taste, ziel_taste)

# -------------------------------------------------------------------------- #
def zieltaste(bahnhof, ziel, zlang):
    """Generiert den Namen der Taste des Zielsignals einer Fahrstrasse. Da aus
    der Zeile der Tabelle nicht ablesbar ist, ob es zum angegebenen (kurzen oder
    langen) Ziel auch das andere gibt, wird gegen die Existenz der Signaltaste
    in den m_daten geprüft.
    :param bahnhof  str  Bahnhof in dem die Fahrstrasse definiert ist
    :param ziel     str  Name des Fahrstrassenziels
    :param zlang    bool True=lange, False=kurze Einfahrt prüfen
    :return string  Name der Taste des Zielsignals
    """
    # generiere Zielsignal-Taste mit kurz/lang Kennung und prüfe deren Existenz
    ziel_taste = name_der_signaltaste(bahnhof, ziel, zlang)
    if zlang:
        # Signal steht in der Spalte mit Schutzweg; prüfe lange Einfahrten
        try:
            _ = m_daten.lange_as[ziel_taste]
        except KeyError:
            # nicht vorhanden -> Zieltaste hat keine kurz/lang Unterscheidung
            ziel_taste = name_der_signaltaste(bahnhof, ziel)

    else:
        # Signal steht in der Spalte ohne Schutzweg, prüfe Signaldaten
        try:
            _ = m_daten.signale[ziel_taste]
        except KeyError:
            # nicht vorhanden -> Zieltaste hat keine kurz/lang Unterscheidung
            ziel_taste = name_der_signaltaste(bahnhof, ziel)

    return ziel_taste

# -------------------------------------------------------------------------- #
def _pruefe_blatt(workbook, bahnhof):
    """Prüft das Tabellenblatt eines Bahnhofs mit den Daten der Fahrstrassen.
    :param workbook Die bereits geöffnete Excel-Datei mit den Blättern.
    :param bahnhof  zu prüfender Bahnhof
    :return         True bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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

    # ---------- SPALTENKÖPFE ----------

    # --- Anzahl der Spalten ist variabel, finde die 1.Spalte jeder Kategorie
    col_sperr = last_col(ws, _ROW_KATEGORIE, COL_FERN) +1    # Sperrschuhe
    col_verschub = last_col(ws, _ROW_KATEGORIE, col_sperr) +1   # Verschubsignale
    col_ek = last_col(ws, _ROW_KATEGORIE, col_verschub) +1  # Eisenbahnkreuzungen
    col_fahrstr = last_col(ws, _ROW_KATEGORIE, col_ek) +2   # Fahrstrassen
    col_signal = last_col(ws, _ROW_KATEGORIE, col_fahrstr) +1   # Signale
    col_gleis = last_col(ws, _ROW_KATEGORIE, col_signal) +1     # Gleisabschnitte
    col_ende = last_col(ws, _ROW_KATEGORIE, col_gleis) +1   # erste unbenutzte

    # --- prüfe die Kategorieköpfe auf Vollständigkeit
    ids = {}        # ids der Elemente in der Spalte {Spalte im Blatt : id}
    sig_von_nach = {}       # {Spalte : (Signalbezeichnung von, nach) }

    # WEICHEN
    elem_fehlen = set(k for k in m_daten.weichen if bahnhof in k)
    # print(f'Folgende Weichen müssen vorhanden sein: {elem_fehlen}.')

    # fernbedient
    wsCol = COL_FERN
    while wsCol < col_sperr:     # Bereich fernbedient
        inhalt = wsGet(ws, _ROW_BEZEICH, wsCol)         # Weichennummer
        if inhalt is None:
            break                   # keine mehr da -> fertig

        t_key = name_der_weichentaste(bahnhof, inhalt)    # Name der Taste
        try:
            elem_fehlen.remove(t_key)   # Weiche gefunden = also fehlt nicht
        except KeyError:                # Weiche nicht definiert!
            print(f' *** Weiche nicht in Weichentabelle: {t_key}')
            fehler = True

        ids[wsCol] = t_key               # Taste für die Spalte wsCol
        # print(f'{wsCol}:{t_key}  ', end='')
        wsCol += 1                  # eine Spalte mehr gefunden

    anz_fern = wsCol - COL_FERN     # Anzahl der fernbedienten Weichen

    # ortsbedient / Sperrschuhe
    wsCol = col_sperr
    while wsCol < col_verschub:  # Bereich ortsbedient
        inhalt = wsGet(ws, _ROW_BEZEICH, wsCol)             # Text ortsbedient
        if inhalt is None:
            break                   # keine mehr da -> fertig

        t_key = inhalt.partition('|')[0]                    # Weichenanteil
        t_key = name_der_weichentaste(bahnhof, t_key[1:])   # Name der Taste
        try:
            elem_fehlen.remove(t_key)   # gefunden = also fehlt nicht
        except KeyError:                # nicht definiert!
            print(f' *** Weiche nicht in Weichentabelle: {t_key}')
            fehler = True

        ids[wsCol] = t_key               # Taste für die Spalte wsCol
        # print(f'{wsCol}:{t_key}  ', end='')
        wsCol += 1                  # eine Spalte mehr gefunden

    anz_sperr = wsCol - col_sperr   # Anzahl der ortsbedienten

    # Fehler bei nicht vorhandener Weiche ausgeben
    if elem_fehlen:              # Menge ist nicht leer
        print(f'\n *** Folgende Weichen fehlen im Sperrenplan: {elem_fehlen}!')
        fehler = True

    # VERSCHUBsignale
    elem_fehlen = set(k for k, v in m_daten.signale.items() \
                      if v[0] in ('AS+VerS', 'VerS') and v[1] == bahnhof)
#     print(f'\nFolgende Signale müssen vorhanden sein: {elem_fehlen}.')
    wsCol = col_verschub
    while wsCol < col_ek:        # Bereich Verschubsignale
        inhalt = wsGet(ws, _ROW_BEZEICH, wsCol)         # Signalbezeichnung
        if inhalt is None:
            break                   # keine mehr da -> fertig

        t_key = name_der_signaltaste(bahnhof, inhalt, False)   # Name Taste kurz
        try:
            elem_fehlen.remove(t_key)       # Signal gefunden = also fehlt nicht
        except KeyError:
            # Signal nicht erwartet! - vielleicht nur eine Taste?
            t_key = name_der_signaltaste(bahnhof, inhalt)   # Name der Taste
            try:
                elem_fehlen.remove(t_key)   # Signal gefunden = also fehlt nicht
            except KeyError:                # nicht erwartetes Signal melden!
                print(f' *** Signal nicht in Signaltabelle: {t_key}')
                fehler = True

        ids[wsCol] = t_key               # Taste für die Spalte wsCol
        # print(f'{wsCol}:{t_key}  ', end='')
        wsCol += 1                  # eine Spalte mehr gefunden

    anz_verschub = wsCol - col_verschub     # Anzahl Verschubsignale

    # Fehler bei nicht vorhandenem Verschubsignal ausgeben
    if elem_fehlen:              # Menge ist nicht leer
        print(f'\n *** Folgende Signale fehlen im Sperrenplan: {elem_fehlen}!')
        fehler = True

    # TODO_Phase3 EK
    anz_ek = 0

    # FAHRSTRASSEN
    wsCol = col_fahrstr
    while wsCol < col_signal:    # Bereich Fahrstrassen
        wsRow = _ROW_START + wsCol - col_fahrstr    # Vergleichszeile

        # Bezeichnungen vergleichen mit Spalte A/B
        inhalt = wsGet(ws, _ROW_BEZEICH, wsCol)     # FS Streckenteil Spalte
        zeile = wsGet(ws, wsRow, COL_STRECKE)       # FS Streckenteil Zeile
        inhalt_gl = wsGet(ws, _ROW_DETAIL, wsCol)   # FS Gleis Spalte
        zeile_gl = wsGet(ws, wsRow, COL_GLEIS)      # FS Gleis Zeile
        if inhalt is None and inhalt_gl is None and \
                zeile is None and zeile_gl is None:
            break                   # keine mehr da -> Fahrstrassen fertig

        if inhalt_gl is None:
            print(f'\n *** Gleis fehlt in Spalte {col_ltr(wsCol)}!')
            fehler = True
        if zeile_gl is None:
            print(f'\n *** Gleis fehlt in Zeile {wsRow}!')
            fehler = True
        if inhalt_gl != zeile_gl:
            print(f'\n *** Gleisbezeichnung: Zeile {wsRow} <> Spalte {col_ltr(wsCol)}!')
            fehler = True
        if inhalt != zeile:
            print(f'\n *** Strecke: Zeile {wsRow} <> Spalte {col_ltr(wsCol)}!')
            fehler = True

        # FS-Start & FS-Ziel für den FS-Schlüssel nötig
        inhalt = wsGet(ws, wsRow, COL_FS_START)     # FS Start
        ziel = wsGet(ws, wsRow, COL_FS_ZIEL_OHNE)   # FS Ziel ohne Schutzweg
        ziel_mit = wsGet(ws, wsRow, COL_FS_ZIEL_MIT)    # FS Ziel mit Schutzweg
        ziel_ist_lang = False
        if ziel is None:
            ziel = ziel_mit
            ziel_ist_lang = True
        elif ziel_mit is not None:
            # Ziel ohne und mit Schutzweg brauchen getrennte Zeilen
            print(f'\n *** Zielsignal in Zeile {wsRow} doppelt vorhanden!')
            fehler = True

        # nur wenn Daten vorhanden kann die ID gebildet werden
        if inhalt is None:
            print(f'\n *** kein Startsignal in Zeile {wsRow} vorhanden!')
            fehler = True
        elif ziel is None:
            print(f'\n *** kein Zielsignal in Zeile {wsRow} vorhanden!')
            fehler = True
        else:
            # --- Starttaste
            # ist nur mit dem Namen gegeben, wir wissen nix über kurze/lange Taste
            t_start = name_der_signaltaste(bahnhof, inhalt)
            try:
                # wir testen mal ob es eine einzige Taste ist
                _ = m_daten.signale[t_start]
            except KeyError:
                # also zu dieser Taste gibt es kein Signal =>
                # somit gibt es Tasten für kurz und lang =>
                # Standard-Start ist die kurze Taste
                t_start = name_der_signaltaste(bahnhof, inhalt, False)

            # --- Zieltaste
            t_ziel = zieltaste(bahnhof, ziel, ziel_ist_lang)
            sig_von_nach[wsCol] = (t_start, t_ziel)     # merke die Signale
            ids[wsCol] = id_fs(t_start, t_ziel)         # Bezeichner Fahrstrasse

        wsCol += 1                  # eine Spalte mehr gefunden

    anz_fahrstr = wsCol - col_fahrstr       # Anzahl Fahrstrassen
    # print(f'\nSchlüssel = {ids}')         # DEBUG
    print(f'\t Anzahl der Fahrstraßen = {anz_fahrstr}', end='')

    # Bevor die gefundenen Fehler nicht behoben sind brauch ma nicht weitermachen
    if fehler:
        print('\n')
        return fehler

    # ---------- INHALT prüfen ----------

    for cntr in range(anz_fahrstr):
        wsRow = _ROW_START + cntr
        zeilen_fehler = False

        # fernbedient
        weichen = {}
        for wsCol in range(COL_FERN, COL_FERN + anz_fern):
            inhalt = wsGet(ws, wsRow, wsCol)     # Stellung Weiche
            if inhalt is None:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Keine Weichenstellung gefunden!')
                zeilen_fehler = True
            elif inhalt == _W_LINKS:
                weichen[ids[wsCol]] = True
            elif inhalt == _W_RECHTS:
                weichen[ids[wsCol]] = False
            elif inhalt != _IST_EGAL:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Weichenstellung nicht erkannt!')
                zeilen_fehler = True

        # ortsbedient
        for wsCol in range(col_sperr, col_sperr + anz_sperr):
            inhalt = wsGet(ws, wsRow, wsCol)     # relevant?
            if inhalt is None:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Relevanz ortsbedienter Weiche/Sperrschuh nicht erkannt!')
                zeilen_fehler = True
            elif inhalt != _IST_EGAL:
                weichen[ids[wsCol]] = True

#        print(f'\nDebug weichen = {weichen}', end='')   # DEBUG
        if not weichen:
            print(f'\n *** Zeile {wsRow}: ' + \
                        'keine relevante Weiche/Sperrschuh wurde erkannt!')
            zeilen_fehler = True

        # Verschubsignal
        signale = set()
        for wsCol in range(col_verschub, col_verschub + anz_verschub):
            inhalt = wsGet(ws, wsRow, wsCol)     # relevant?
            if inhalt is None:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Relevanz des Verschubsignals nicht erkannt!')
                zeilen_fehler = True
            elif inhalt != _IST_EGAL:
                signale.add(ids[wsCol])

#        print(f'\t Debug signale = {signale}', end='')   # DEBUG

        # TODO_Phase3 EK
        ek = set()
        for wsCol in range(col_ek, col_ek + anz_ek):
            pass

        # Fahrstrassen-Ausschluss
        fs = set()
        for wsCol in range(col_fahrstr, col_fahrstr + anz_fahrstr):
            eigen = cntr == wsCol-col_fahrstr   # sind in eigener Spalte
            inhalt = wsGet(ws, wsRow, wsCol)    # relevant?
            if inhalt is None:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Relevanz der Fahrstrasse nicht erkannt!')
                zeilen_fehler = True

            elif inhalt == _FS_SELBST:
                if not eigen:       # darf aber nur in der eigenen Spalte sein!
                    print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                            'Selbstausschluss an falscher Stelle!')
                    zeilen_fehler = True
                # Selbstausschluss darf nicht eingetragen werden!

            elif inhalt == _FS_AUS:
                if eigen:
                    print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                            'Ausschluss statt Selbstausschluss angegeben!')
                    zeilen_fehler = True
                else:
                    fs.add(ids[wsCol])

            elif inhalt != _FS_OK:
                print(f'\n *** Zelle {col_ltr(wsCol)}{wsRow}: ' + \
                        'Ungültiger Eintrag bei Fahrstrasse erkannt!')
                zeilen_fehler = True

#         print(f'\t Debug fs-ausschluss = {fs}', end='')   # DEBUG

        # Gleisabschnitte der Fahrstrasse
        fszss = None
        gleise = set()
        for wsCol in range(col_gleis, col_ende):
            inhalt = wsGet(ws, wsRow, wsCol)
            if inhalt is None:
                if wsCol == col_gleis:  # 1. Feld leer, das darf nicht
                    print(f'\n *** Zelle {col_ltr(col_gleis)}{wsRow}: ' + \
                            'keine Fahrstrassen-Zugschlussstelle gefunden!')
                    zeilen_fehler = True
                break   # auf jeden Fall erwarten wir nix mehr, da leer

            # Gleisbezeichnung generieren, prüfen, und der Liste hinzufügen
            gleis = name_gleis(bahnhof, inhalt)
            try:
                _ = m_daten.gleis[gleis]    # wenn erfolgreich ist Gleisabschnitt definiert
                gleise.add(gleis)
                if wsCol == col_gleis:      # 1. Feld ist die FSZSS
                    fszss = gleis

            except KeyError:
                # nicht vorhanden -> Gleisabschnitt nicht definiert -> Fehler
                print(f'\n *** Zelle {col_ltr(col_gleis)}{wsRow}: ' + \
                        f'Gleis {gleis} für Fahrstrasse ist nicht definiert!')
                zeilen_fehler = True

        # Programmdaten übergeben
        if zeilen_fehler:
            fehler = True
            continue        # problematischen Datensatz nicht übernehmen

        # aber jetzt
        idx = col_fahrstr + cntr
        fehler |= m_daten.neu_fahrstrasse(ids[idx], sig_von_nach[idx], \
                    weichen, signale, ek, fs, gleise, fszss)

    if not fehler:
        print(' ... ok')
    return fehler

# -------------------------------------------------------------------------- #
def pruefe(workbook):
    """Prüft die Tabellenblätter mit den Daten der Fahrstrassen.
    :param workbook Die bereits geöffnete Excel-Datei.
    :return         True bei einem Fehler; sonst False
    """
    fehler = False

    print(f'\nFahrstrassenprüfung - folgende Bahnhöfe gefunden: {m_daten.bahnhofset()}')
    for b in m_daten.bahnhofset():
        fehler |= _pruefe_blatt(workbook, b)

    # abschließende Konsistenzprüfung nach Prüfung aller Bahnhöfe
    return m_daten.fs_konsistenz() | fehler

# ------------------------------------------------------------- Ende Gelände #

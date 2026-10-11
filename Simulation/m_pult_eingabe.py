#!/usr/local/bin/python3.6
# -*- coding: utf-8
"""
Einlesen der Tasten von den Platinen.
Als Hauptprogramm gestartet: Testfunktion für IO Pi Plus in Modul-Umgebung.
"""
# !/usr/bin/env python # würde nur das Standard-Python 3.5.3 ausführen
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-11 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# 0.6 2020-10-04 wh zum Testen lauffähig gemacht (ersetzt B_IOPi_Test)
# -------------------------------------------------------------------------- #

from time import monotonic

# from m_common import TastenTyp
from m_ausgaben import MeldeTyp as MTyp, melde, setze_print_grad, setze_proto_grad
import m_pult_ausgabe
import m_basis
from daten_basis import Melder, Taste

# -------------------------------------------------- modulweite Definitionen #
_TEST_PLATIN_ZAHL = 1   # bei Test: Anzahl IO Pi Module die zu testen sind

# --- Konstante
_PRELL_DAUER = 0.2      # Zeit [s]
_STOER_DAUER = 9.9      # bis die Taste als gestört betrachtet wird
_TASTENSTOER_BLINKER = 'Tastenstoerung'

# --- Variable
_produktiv = True       # Produktivlauf (im Gegensatz zur Testfunktion)
_mit_platin = False     # False=Testen am Bildschirm; True=verwende Elektronik
entprellzeit = -1       # Ende der Entprellzeit
_t_stoer = {}           # zum Erkennen gestörter Tasten
_stoer_blinker_an = False
_hw = None

# Tasten - *0 hat TastenTyp >= *1
tz0 = Taste.NIX     # zuletzt verarbeitete Kombi
tz1 = Taste.NIX
tg0 = Taste.NIX     # gelesene Kombi vor entprellen
tg1 = Taste.NIX
t2nix = (Taste.NIX, Taste.NIX)

# ----------------------------------------------------------------- Methoden #
def init(in_echt):
    """Initialisierung der Eingabe; für Platinen die Zuordnung der I/O Ports, etc.
    :param  in_echt   bool    False=Testen am Bildschirm; True=verwende Elektronik
    """
    global _mit_platin
    _mit_platin = in_echt

    if _mit_platin:
        # nur importieren wenn auch Platinen vorhanden sind
        from c_iopi import EingabeHardware      # pylint: disable=import-outside-toplevel
        global _hw
        _hw = EingabeHardware(m_basis.max_tast_kanal if _produktiv \
                              else 32 * _TEST_PLATIN_ZAHL -1)

    else:
        pass

# -------------------------------------------------------------------------- #
def _input_taste(beschr=''):
    """Einlesen einer Taste über die Tastatur.
    :param  beschr  Beschreibung der Taste
    :return Taste.*
    """
    while True:
        tstr = input(f'Taste {beschr}: ')
        if not tstr:
            return Taste.NIX    # keine Eingabe

        try:                    # suche Taste zum Namen
            return Taste[tstr]
        except KeyError:
            melde(MTyp.WARN, f'keine solche Taste: {tstr} !')

# -------------------------------------------------------------------------- #
def _test_tasten():
    """Einlesen von bis zu zwei Tasten über die Tastatur.
    """
    t = _input_taste('A')
    if t == Taste.NIX:
        return (t, t)

    return (t, _input_taste('B'))

# -------------------------------------------------------------------------- #
def _test_tastenstoerung(*tasten):
    """Testet ob eine der Tasten gestört ist.
    :param  *t      Taste   zu prüfende Tasten
    :return bool    True wenn eine Taste gestört ist
    """
    global _t_stoer
    neu = {}      # die neuen Ablaufzeiten

    # über alle gegebenen Tasten
    for t in tasten:
        if t != Taste.NIX:      # nicht gedrückte Tasten dürfen nicht geprüft werden!
            try:
                # taste schon vorhanden, dann die bisherige Zeit nehmen
                neu[t] = _t_stoer[t]
            except KeyError:
                # unbekannte Taste, Störzeitablauf setzen
                neu[t] = monotonic() + _STOER_DAUER

    # neu{} ist damit die aktualisierten Version von _t_stoer
    _t_stoer = neu      # damit sind alle nicht (mehr) gedrückten Tasten gelöscht

    stoer_alarm = False
    for t, zeit in _t_stoer.items():
        if monotonic() > zeit:
            # Taste gestört!
            melde(MTyp.WARN, f'Taste {t} als gestört erkannt!')
            stoer_alarm = True

    global _stoer_blinker_an
    if stoer_alarm:
        # Tastenstörmelder ist notwendig aber noch nicht gestartet
        if not _stoer_blinker_an:
            _stoer_blinker_an = True
            if _produktiv:
                m_pult_ausgabe.blinken_start(_TASTENSTOER_BLINKER, Melder.T.value, -1)
            else:
                melde(MTyp.DEBUG, '-> Störblinker an')

    else:
        # Tastenstörmelder abschalten wenn läuft
        if _stoer_blinker_an:
            _stoer_blinker_an = False
            melde(MTyp.DEBUG, 'Tastenstörung beendet.')
            if _produktiv:
                m_pult_ausgabe.blinken_stop_regular(_TASTENSTOER_BLINKER)
                m_pult_ausgabe.schalte_melder(Melder.T, False)

    return stoer_alarm

# -------------------------------------------------------------------------- #
def gedrueckte_tasten():
    """Liefert die beiden Tasten zurück, welche verarbeitet werden sollen.
    Diese sind entprellt und neu = sie unterscheiden sich von den letzten Tasten.
    :return (t0,t1) zwei Tasten, sortiert nach fallendem TastenTyp (t0.typ > t1.typ).
    """
    # pylint: disable=too-many-return-statements
    # schrittweise Tests ob die weitere Verarbeitung erlaubt ist

    # Platinen oder Test
    if _mit_platin:
        try:
            ta0, ta1 = _hw.hole_tasten()
        except ValueError:
            return t2nix
    else:
        ta0, ta1 = _test_tasten()

    # Analyse ob eine Taste gestört ist, dann darf nix verarbeitet werden!
    if _test_tastenstoerung(ta0, ta1):
        return t2nix

    # sortieren
    if ta1.typ > ta0.typ:
        ta1, ta0 = ta0, ta1

    # sind überhaupt Tasten zu verarbeiten?
    global tg0, tg1, tz0, tz1, entprellzeit
    if ta0 == Taste.NIX:
        # keine Taste gedrückt -> merken und fertig
        tg0, tg1 = Taste.NIX, Taste.NIX
        tz0, tz1 = Taste.NIX, Taste.NIX
        return t2nix

    # entprellen: Tasten vergleichen, ggf. merken
    melde(MTyp.DEBUG, 'Tasten entprellen')
    # mono = monotonic()  # for debug
    if ta0 != tg0 or ta1 != tg1:
        # an den Tasten hat sich etwas geändert -> Tasten und Zeit merken, fertig
        tg0, tg1 = ta0, ta1

        if _mit_platin:
            # nur bei der Elektronik ist entprellen notwendig
            entprellzeit = monotonic() + _PRELL_DAUER
            # entprellzeit = mono + _PRELL_DAUER     # for debug
            # melde(MTyp.DEBUG, f'..NEU.... mono-zeit = {mono}  .. entprellt = {entprellzeit}')
            return t2nix

    # also gleiche Tasten wie zuvor -> noch in der Entprellzeit?
    # melde(MTyp.DEBUG, f'..PRÜF... mono-zeit = {mono}  .. entprellt = {entprellzeit}')
    # if mono < entprellzeit:       # for debug
    if monotonic() < entprellzeit:
        # müssen noch warten
        return t2nix

    # also Entprellzeit bereits abgelaufen
    melde(MTyp.DEBUG, 'Tasten entprellt!')
    if tg0 == tz0 and tg1 == tz1:
        # Tasten wurden schon verarbeitet!
        return t2nix

    # wir haben also neue Tasten zu verarbeiten!
    melde(MTyp.DEBUG, 'neue Tasten sind da!')
    tz0, tz1 = ta0, ta1
    return (tz0, tz1)

# -------------------------------------------------------------------------- #
# Für Testzwecke kann das Modul auch alleine
if __name__ == "__main__":

    # Protokoll Ebenen
    setze_print_grad(MTyp.INFO)         # je nach Bedarf
    setze_proto_grad(MTyp.WARN)         # je nach Bedarf
    melde(MTyp.IMMER, '*** Starte IO Pi Plus Testsuite ***')
    melde(MTyp.INFO, '(m_pult_eingabe.py)    Ende mit Strg-C')

    # Initialisierung Hardware
    init(True)

    # ausführen bis Strg-C oder Stop gedrückt wird
    try:
        while True:
    #         m_pult_ausgabe.liste_leds()       # ggf. debuggen
    #         m_basis.show_all_stati()          # ggf. debuggen
            # ausführen der Routinen
            t0, t1 = gedrueckte_tasten()

            if t0 == Taste.NIX:
                continue

            melde(MTyp.INFO, f'Taste 0 = {t0}, Taste 1 = {t1}')

            if t0 == Taste.Stop:
                break

    except (KeyboardInterrupt, EOFError):
        pass

    # aus und vorbei
    melde(MTyp.IMMER, '*** IO Pi Plus Testsuite beendet ***')

# ------------------------------------------------------------- Ende Gelände #

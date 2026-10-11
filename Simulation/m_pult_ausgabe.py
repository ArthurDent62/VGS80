#!/usr/local/bin/python3.6
# -*- coding: utf-8
"""
Steuerung der Ausgabe, noch unabhängig von der konkreten Hardware.
Als Hauptprogramm gestartet: Testfunktion für TLC-Platinen in Modul-Umgebung.
"""
# !/usr/bin/env python # würde nur das Standard-Python (3.5.3) ausführen
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-11 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# 0.6 2020-10-09 wh zum Testen lauffähig gemacht (ersetzt B_TLC_Test)
# -------------------------------------------------------------------------- #

import inspect
import math
import threading
import time

from m_ausgaben import MeldeTyp as MTyp, melde, setze_print_grad, setze_proto_grad
import m_basis
from daten_basis import Melder

# -------------------------------------------------- modulweite Definitionen #
# --- Konstante
_BLINK_DAUER = 1.0                  # [s] Dauer einer Blinkphase (an oder aus)
_BLINK_THREAD_NAME = 'Die Blinkspannung'
_BLINKSPANNUNG_BLINKER = 'BLÜM'     # Name des Blinkspannung-Überprüfung-Melder
_BLINKSPANNUNG_ZEIT = 10.0          # [s] wie lange der BLÜM blinkt während der Prüfung

# --- Modul-Objekte und Variablen
_mit_platin = False     # False=Testen am Bildschirm; True=verwende Elektronik
_led_ein = []           # Array von Wahrheitswerten für den Status jeder LED
                            # ...falls keine Hardware angeschlossen ist
_blinkende_leds = {}    # derzeit blinkende LED
_blink_ist_an = False   # ist die Blinkspannung derzeit an?
_ahw = None                # Ausgabe-Hardware

# Semaphoren, Events, Threads
_blink_run_event = None     # lösche dieses Event um die Blinkspannung zu beenden
_blink_thread = None        # Thread der Blinkspannung
_blinker_sema = threading.BoundedSemaphore(1)    # Einstellungen beim Blinker
_ausgabe_sema = threading.BoundedSemaphore(1)    # Änderungen beim Schaltzustand der LEDs

# ----------------------------------------------------------------- Methoden #
def init(in_echt):
    """Initialisierung der Ausgabe; für Platinen die Zuordnung der I/O Ports, etc.
    :param  in_echt    bool    False=Testen am Bildschirm; True=verwende Elektronik
    """
    global _mit_platin, _led_ein, _blink_run_event, _blink_thread
    _mit_platin = in_echt

    if _mit_platin:
        # nur importieren wenn auch Platinen vorhanden sind
        from c_tlc5947 import AusgabeHardware   # pylint: disable=import-outside-toplevel
        global _ahw
        _ahw = AusgabeHardware(m_basis.max_led_kanal)

    else:
        melde(MTyp.INFO, f'ausgabe.init: max. led kanal = {m_basis.max_led_kanal}')
        _led_ein = [False] * (1 + m_basis.max_led_kanal)

    # einschalten vom Netz-Melder
    schalte_melder(Melder.N, True)

    # starten der Blinkspannung
    _blink_run_event = threading.Event()
    _blink_run_event.set()
    melde(MTyp.DEBUG, f"Status des 'blink_run_event' = {_blink_run_event.is_set()}")

    _blink_thread = threading.Thread(name=_BLINK_THREAD_NAME, target=_blinken_lassen)
    _blink_thread.start()

# -------------------------------------------------------------------------- #
def heller(bHell):
    """Ändert die Helligkeit der LEDs um eine Stufe.
    :param  bHell   bool    True = eine Stufe heller; False ist dünkler
    """
    if _mit_platin:
        _ahw.helligkeit(bHell)
    else:
        melde(MTyp.INFO, f'LED-Helligkeit = {"heller" if bHell else "dünkler"}')

# -------------------------------------------------------------------------- #
def schalte_led(kanal, bEin):
    """Schaltet die LED auf Kanal kanal ein oder aus.
    :param  kanal   int     Kanal der LED
    :param  bEin    bool    True=einschalten, False=ausschalten
    """
    if kanal > m_basis.max_led_kanal:
        melde(MTyp.FEHLER, f'LED mit Kanal-Nr. {kanal} ist nicht vorhanden')
        return

    if _mit_platin:
        _ahw.led_schalten(kanal, bEin)
    else:
        _led_ein[kanal] = bEin

# -------------------------------------------------------------------------- #
def schalte_melder(melder, bEin):
    """Schaltet einen Melder ein oder aus.
    :param  melder  Melder  der zu schaltende Melder
    :param  bEin    bool    True=einschalten, False=ausschalten
    """
    # pylint: disable=not-an-iterable
    # denn es ist ein Tupel
    for k in melder.value:
        if k:
            schalte_led(k, bEin)

# -------------------------------------------------------------------------- #
def _blinken_lassen():
    """Funktion, die der Thread der Blinkspannung abarbeitet.
    """
    global _blink_ist_an, _blink_run_event

    fu_name = inspect.currentframe().f_code.co_name

    while _blink_run_event.is_set():

        # neuen blink-status setzen
        _blink_ist_an = not _blink_ist_an
        melde(MTyp.DEBUG, f'{fu_name}(): _blink_ist_an:{_blink_ist_an} * ' \
              + f'_blinkende_leds:{_blinkende_leds} *')

        # Blinker abarbeiten
        aendern_erlaubt()       # nun dürfen nur wir die LEDs ändern

#        print(f'_blinken_lassen: warte auf _blinker_sema')
        with _blinker_sema:
#            print(f'_blinken_lassen: bin drin')

            for name, v in list(_blinkende_leds.items()):
                k0, k1, anzahl, cb_ende = v

                # endet dieser Blinker?
                if anzahl == 0:
                    # Blinker löschen
                    del _blinkende_leds[name]

                    # Callback Routine ausführen, wenn definiert
                    if cb_ende is not None:
                        cb_ende()

                    continue            # das wars hier, nächster Blinker

                # also dieser Blinker geht weiter
                schalte_led(k0, _blink_ist_an)
                if k1 is not None:
                    schalte_led(k1, _blink_ist_an)

                # Für endliche Blinker, die Zahl offener Blinks reduzieren
                if anzahl > 0:
                    anzahl -= 1
                    _blinkende_leds[name] = (k0, k1, anzahl, cb_ende)

        aendern_fertig()     # Änderung aktivieren

#        print(f'_blinken_lassen: bin raus')
#        melde(MTyp.DEBUG, 'Blinker-Sema wieder frei')

        # schlafen bis es wieder blinken soll
        time.sleep(_BLINK_DAUER)

#         melde(MTyp.DEBUG, f'{fu_name}(): _run_event:{_blink_run_event.is_set()}')

    # Event wurde gelöscht, Thread wird beendet
    melde(MTyp.IMMER, _BLINK_THREAD_NAME + ' wurde beendet')

# -------------------------------------------------------------------------- #
def blinken_start(name, kanal, anzahl, cb_ende=None):
    """Lässt die LED auf Kanal kanal blinken. Untersucht den aktuellen Zustand
    und schaltet sofort um. Erwartet dass bereits aendern_erlaubt() ist.
    :param  name    str     Name des Blinkers
    :param  kanal   int     Kanal der LED (or (int,int)-tuple)
    :param  anzahl  int     Anzahl der Wechselvorgänge, oder -1 für immer
    :param  cb_ende func    Funktion die nach Ende aller Wechsel aufgerufen wird
    """
    global _blink_ist_an, _blinkende_leds

    if isinstance(kanal, int):
        k0 = kanal
        k1 = None
    else:
        k0, k1 = kanal

    # prüfen der Kanäle
    fu_name = inspect.currentframe().f_code.co_name
    if k0 > m_basis.max_led_kanal:
        melde(MTyp.FEHLER, f'{fu_name}(): LED mit Kanal-Nr. {k0} nicht vorhanden')
        return

    if k1 is not None and k1 > m_basis.max_led_kanal:
        melde(MTyp.FEHLER, f'{fu_name}(): 2.LED mit Kanal-Nr. {k1} nicht vorhanden')
        return

    # die neuen LEDs in den aktuellen Blink-Zustand versetzten
    print(f'blinken_start: warte auf _blinker_sema')
    with _blinker_sema:
        print(f'blinken_start: bin drin')
        schalte_led(k0, _blink_ist_an)
        if k1 is not None:
            schalte_led(k1, _blink_ist_an)

        # zur Liste aktiver Blinke-LEDs hinzufügen
        _blinkende_leds[name] = (k0, k1, anzahl, cb_ende)

    print(f'blinken_start: bin raus')
    melde(MTyp.DEBUG, f'neuer Blinker: {name}\n\tgesamt: {_blinkende_leds}')

# -------------------------------------------------------------------------- #
def blinken_stop_regular(name):
    """Beendet einen Blinker aus dem HauptThread heraus.
    Erwartet dass bereits aendern_erlaubt() ist.
    :param  name    str     Name des Blinkers
    """
    melde(MTyp.DEBUG, f'Ende für {name}; Blinker aktiv={_blinkende_leds}')

    # entferne Blinker aus der Liste, hole seine Daten
    print(f'blinken_stop_regular: warte auf _blinker_sema')
    with _blinker_sema:
        print(f'blinken_stop_regular: bin drin')
        try:
            _, _, _, cb_ende = _blinkende_leds.pop(name, None)
        except KeyError:
            melde(MTyp.DEBUG, f'Blinker {name} nicht vorhanden!')
            return        # keine Daten zu Blinker vorhanden
        except ValueError:
            melde(MTyp.FEHLER, f'Daten zum Blinker {name} waren inkonsistent!')
            return        # wir machen einfach weiter

        # callback abarbeiten bevor der Blinker Timer wieder zugelassen wird
        if cb_ende is not None:
            cb_ende()

    print(f'blinken_stop_regular: bin raus')

# -------------------------------------------------------------------------- #
# def blinken_stop_threaded(name):
#     """Beendet einen Blinker aus einem asynchronen Thread heraus.
#     :param  name    str     Name des Blinkers
#     """
#     # asynchron -> zuerst Anfrage Änderungen erlaubt stellen
#     aendern_erlaubt()
#     blinken_stop_regular(name)
#     aendern_fertig()     # Änderungen aktivieren und Erlaubnis zurückgeben

# -------------------------------------------------------------------------- #
def bluem_ein():
    """Einschalten des BlÜM für die vorgesehene Dauer.
    """
    blinken_start(_BLINKSPANNUNG_BLINKER, Melder.BlÜM.value, \
                  math.ceil(_BLINKSPANNUNG_ZEIT / _BLINK_DAUER), cb_ende=bluem_aus)
    m_basis.blinkspannung = True

# -------------------------------------------------------------------------- #
def bluem_aus():
    """BlÜM endet - LED abschalten.
    """
    # pylint: disable=not-an-iterable
    # denn es ist ein Tupel
    m_basis.blinkspannung = False
    schalte_melder(Melder.BlÜM, False)

# -------------------------------------------------------------------------- #
def liste_leds(melde_typ=MTyp.DEBUG):
    """Listet den Zustand der LEDs auf - für Entwicklung gemacht.
    :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
    """
    # z = ''.join('1' if on else '0' for on in _led_ein)
    # z = ''.join(str(on) for on in _led_ein * 1)

    z = ''
    grp = 6
    brd = 4

    # Zusammenstellung des Debug-Strings
    if _mit_platin:
        for k in range(1 + m_basis.max_led_kanal):
            if k%(grp*brd) == 0:
                z += ':'
            elif k%grp == 0:
                z += '.'
            z += '1' if _ahw.ist_led_ein(k) else '0'

    else:
        for g in [_led_ein[i:i+grp] for i in range(0, len(_led_ein), grp)]:
            z += ''.join('1' if on else '0' for on in g)
            z += '.' if (1+len(z))//(grp+1)%brd else ':'

    melde(melde_typ, 'led status: ' + z)

# -------------------------------------------------------------------------- #
def aendern_erlaubt():
    """Anfrage bevor Änderungen durchgeführt werden können; ist zwingend
    durchzuführen damit Änderungen verschiedener Programmteile sich nicht
    gegenseitig überschreiben.
    """
    # Anfrage ob / warten bis Änderungen zulässig
    _ausgabe_sema.acquire()

# -------------------------------------------------------------------------- #
def aendern_fertig():
    """Durchführen der gespeicherten Änderungen auf den Boards (im Test: im RAM);
    ist zwingend am Ende von Ausgabeänderungen durchzuführen um andere wieder
    zuzulassen.
    """
    if _mit_platin:
        _ahw.leds_nun_aendern()
    else:
        liste_leds()

    # Änderungen wieder für andere zulassen
    _ausgabe_sema.release()

# -------------------------------------------------------------------------- #
def abschalten():
    """Schalte die LEDs und Blinker ab.
    """
    global _blink_run_event, _blink_thread

    # zunächst die Blinkspannung abschalten
    _blink_run_event.clear()

    # anschließend die LEDs ausschalten
    if _mit_platin:
        _ahw.abschalten()

    else:
        aendern_erlaubt()
        for kanal in range(1 + m_basis.max_led_kanal):
            schalte_led(kanal, False)

        aendern_fertig()    # schließlich übernehmen

    # noch kurz auf den Blinkspannungsthread warten
    _blink_thread.join(_BLINK_DAUER)
    if _blink_thread.is_alive():
        melde(MTyp.FEHLER, _BLINK_THREAD_NAME + ' war nicht zu stoppen!')

# -------------------------------------------------------------------------- #
# Für Testzwecke kann das Modul auch alleine
if __name__ == "__main__":

    # Protokoll Ebenen
    setze_print_grad(MTyp.INFO)         # je nach Bedarf
    setze_proto_grad(MTyp.WARN)         # je nach Bedarf
    melde(MTyp.IMMER, '*** Starte TLC Testsuite ***')
    melde(MTyp.INFO, '(m_pult_ausgabe.py)    Ende mit Strg-C')
    melde(MTyp.INFO, 'Modus: Ein=E - Aus=A - Blink=B - Reihe=R - Testen=T - Helligkeit=H')

    # Initialisierung Hardware
    TEILER = {1, 2, 3, 4, 6, 8, 12, 24}
    MAX_KANAL = 6*24 -1                 # maximal getestete Kanalnummer
    m_basis.max_led_kanal = MAX_KANAL
    init(False)          # mit echten platinen (oder nicht?)

    # ausführen bis Strg-Z gedrückt wird
    try:
        while True:
            #if not _mit_platin:
            liste_leds(MTyp.INFO)
            modus = input('Modus (E/A/B/R/T/H/Strg-C): ').upper()

            # ausführen der Routinen
            aendern_erlaubt()

            if modus == 'E':
                ledkanal = int(input(f'Kanal (0-{MAX_KANAL}) ein: '))
                schalte_led(ledkanal, True)

            elif modus == 'A':
                ledkanal = int(input(f'Kanal (0-{MAX_KANAL}) aus: '))
                schalte_led(ledkanal, False)

            elif modus == 'H':
                delta = input('Helligkeit +/-: ')
                heller(delta == '+')

            elif modus == 'B':
                ledkanal = int(input(f'Kanal (0-{MAX_KANAL}) blink: '))
                anz = int(input('Anzahl (-1 für unbeschränkt, 0 für Ende): '))
                blink_name = f'Blinker_{ledkanal:03}'
                if anz == 0:
                    blinken_stop_regular(blink_name)
                else:
                    blinken_start(blink_name, ledkanal, anz)

            elif modus == 'R':
                submod = input('L=Laufend, B=mit Bestätigung): ').upper()
                for kan in range(MAX_KANAL+1):
                    schalte_led(kan, True)
                    aendern_fertig()
                    print(f'Kanal {kan:03} ist an ', end='')

                    if submod == 'B':
                        input(', weiter?')

                    else:
                        # kleine Pause
                        for _ in range(4):
                            print('. ', end='', flush=True)
                            time.sleep(0.5)
                        print('und aus!')

                    # LED wieder ausschalten
                    aendern_erlaubt()
                    schalte_led(kan, False)
                    aendern_fertig()
                    aendern_erlaubt()

            elif modus == 'T':
                kan_diff = int(input(f'Abstand der Kanäle ({TEILER}): '))
                if kan_diff not in TEILER:
                    continue    # wir arbeiten nur mit diesen Offsets

                for anfang in range(kan_diff):
                    print('Kanal an für ', end='')

                    for kan in range(anfang, MAX_KANAL+1, kan_diff):
                        schalte_led(kan, True)
                        print(f'{kan:03}, ', end='')
                    aendern_fertig()

                    # warten auf Bestätigung
                    _ = input('Weiter mit <Eingabe>: ')

                    # LED wieder ausschalten
                    aendern_erlaubt()
                    for kan in range(anfang, MAX_KANAL+1, kan_diff):
                        schalte_led(kan, False)
                    aendern_fertig()        # rausschreiben
                    aendern_erlaubt()       # Status wie am Anfang der Schleife

            else:
                melde(MTyp.WARN, 'unbekannter Modus: ' + modus)

            aendern_fertig()

    except (KeyboardInterrupt, EOFError):
        pass

    # aus und vorbei
    print()
    abschalten()
    melde(MTyp.IMMER, '** TLC Testsuite beendet **')

# ------------------------------------------------------------- Ende Gelände #

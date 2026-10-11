"""
Testen der Blinkspannung.
"""
# -------------------------------------------------------------------------- #
# (c) 2020 Walter Haschka
#
# Versionen
# 0.0 2020-01-10 wh Test begonnen
# -------------------------------------------------------------------------- #

from threading import BoundedSemaphore, Event, Thread    # Timer
import time

# import inspect

# from m_ausgaben import MeldeTyp as MTyp, melde
# import m_basis
# from daten_basis import Melder

# -------------------------------------------------- modulweite Definitionen #
# --- Konstante
_BLINK_DAUER = 1.0                  # [s] Dauer einer Blinkphase (an oder aus)
# _BLINKSPANNUNG_BLINKER = 'BLÜM'     # Name des Blinkspannung-Überprüfung-Melder
# _BLINKSPANNUNG_ZEIT = 10.0          # [s] wie lange der BLÜM blinkt während der Prüfung

# --- Modul-Objekte und Variablen
blink_run_event = None     # lösche Event um die Blinkspannung zu beenden
blink_thread = None
# _mit_platin = False     # False=Testen am Bildschirm; True=verwende Elektronik
# _led_ein = []            # Array von Wahrheitswerten für den Status jeder LED
                            # # ...falls keine Hardware angeschlossen ist
_blinkende_leds = {}    # derzeit blinkende LED
_blink_ist_an = False   # ist die Blinkspannung derzeit an?
# _ahw = None                # Ausgabe-Hardware

# # Semaphoren gegen den gleichzeitigen Zugriff auf Daten
_blinker_sema = BoundedSemaphore(1)    # Einstellungen beim Blinker
# _ausgabe_sema = BoundedSemaphore(1)    # Änderungen beim Schaltzustand der LEDs

# ----------------------------------------------------------------- Methoden #


# -------------------------------------------------------------------------- #
def _blinken_lassen():
    """Funktion vom Thread der Blinkspannung.
    """
    global _blink_ist_an, blink_run_event

    # check initial state
    print(f'Blinkspannung: {blink_run_event} ist {blink_run_event.is_set()}')

    while blink_run_event.is_set():
        _blink_ist_an = not _blink_ist_an
        print(f'Status Blinker: {_blink_ist_an:<5} ', end='')

        with _blinker_sema:
            for b, v in list(_blinkende_leds.items()):
                o, t, l = v
                print(f'b:{b} & l:{l} - ', end='')

                if l == 0:
                    del _blinkende_leds[b]
                else:
                    _blinkende_leds[b] = (o, t, l-1)
            print()

            # hier könnte man noch mehr machen

        time.sleep(_BLINK_DAUER)

    print(f'Blinkspannung: OVER - AND - OUT\n')

# -------------------------------------------------------------------------- #
def abschalten():
    """Schalte die LEDs und Blinker ab.
    """
    global blink_run_event, blink_thread
    blink_run_event.clear()

    # warte
    print(f'abschalten 0 - warte auf Blinkspannung-Thread')
    blink_thread.join(10)

    # waiting finished
    print(f'abschalten 1 - Thread beendet oder Timeout abgelaufen')

# -------------------------------------------------------------------------- #
def blinken_start(name):
    """Fügt neuen 'Blinker' hinzu.
    """
    global _blinkende_leds
    with _blinker_sema:
        _blinkende_leds[name] = (ord(name[0]), time.monotonic(), len(name))
#         print(_blinkende_leds)
        time.sleep(.5)

# -------------------------------------------------------------------------- #
def blinken_aus(name):
    """Entfernt einen 'Blinker'.
    """
    with _blinker_sema:
        try:
            del _blinkende_leds[name]
        except KeyError:
            pass

        time.sleep(.5)

# -------------------------------------------------------------------------- #
def _blinkspannung_starten():                         # -> m_pult_ausgabe.init
    """Startet den Thread für die Blinkspannung.
    """
    global blink_thread, blink_run_event
    blink_run_event = Event()
    blink_run_event.set()
    print(f'main-event: {blink_run_event} ist {blink_run_event.is_set()}')

    blink_thread = Thread(name='Blinkspannung', target=_blinken_lassen)
    blink_thread.start()

# ------------------------------------------------------------------- main() #

# init vom Hauptteil
print('----- Test startet! - Ende mit Strg-Z')
_blinkspannung_starten()

# zentrales Tun
try:
    while True:
        # ausführen der Routinen
        # aendern_erlaubt()
        tstr = input()
        if tstr[0] == '+':
            blinken_start(tstr[1:])

        elif tstr[0] == '-':
            blinken_aus(tstr[1:])

        else:
            print('dont know what to do with '+tstr)

        # aendern_fertig()

    # tstr = input(f'   ***   Ende mit Strg-Z   ***')

# # ausführen bis Strg-C gedrückt wird
except (KeyboardInterrupt, EOFError):
    pass

# Abschluss
print('----- Test endet!')
abschalten()
print('----- Test beendet!')

# dt = {'ali':(0,1,4), 'josi':(2,5,8), 'bertl':(3,6,9)}
# for a, b, c, d in dt.items():
#     print(a, b, c, d)
# ------------------------------------------------------------- Ende Gelände #

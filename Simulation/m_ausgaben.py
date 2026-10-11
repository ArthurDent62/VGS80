"""
Ausgeben und Protokollieren von Meldungen diverser Qualitätsstufen.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# WICHTIG:
# Tunlichst kein anderes eigenes Modul importieren, um zirkuläre Importe zu vermeiden.
#
# Versionen
# 0.0 2019-04-05 wh Modul begonnen - zusammenführen aller vorhandenen Meldungen
#                    in dieses Modul
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from sys import stdout, stderr
import time
from enum import Enum, auto, unique
import codecs

# -------------------------------------------------- modulweite Definitionen #
# --- Konstante
_DATEI_PROTO_NAME = 'Simulation_'
_DATEI_PROTO_EXT = '.log'

# --- Variable

# -------------------------------------------------------------------------- #
@unique
class MeldeTyp(Enum):
    """Unterscheidung der Qualität, der Wichtigkeit der Meldungen.
    """
    # pylint: disable=bad-whitespace
    # erhöht hier die Lesbarkeit
    # WICHTIG: nach Kritikalität ordnen wegen Protokoll-Detailgrad
    DEBUG   = auto()    # debug eben
    INFO    = auto()    # Information (unkritisch)
    WARN    = auto()    # Warnung (das sollte irgendwie nicht so sein)
    FEHLER  = auto()    # Fehler (das ist schlecht)
    FATAL   = auto()    # (da geht ehrlich nix mehr)
    IMMER   = auto()    # wird immer protokolliert

# --- Variable
_print_grad = MeldeTyp.INFO.value
_proto_grad = MeldeTyp.FEHLER.value

# -------------------------------------------------------------------------- #
def setze_proto_grad(ab_typ=MeldeTyp.FEHLER):
    """Ändert den Detailgrad vom Protokoll.
    """
    # merke Detailgrad
    global _proto_grad
    _proto_grad = ab_typ.value

# -------------------------------------------------------------------------- #
def setze_print_grad(ab_typ=MeldeTyp.INFO):
    """Ändert den Detailgrad vom Protokoll.
    """
    # merke Detailgrad
    global _print_grad
    _print_grad = ab_typ.value

# -------------------------------------------------------------------------- #
def melde(typ, text):
    """Ausgabe des Textes der Meldung auf dem Ausgabemedium und Aufnahme ins
    Protokoll abhängig vom MeldeTyp.
    """
    # vorbereiten
    fmt_kurz = '%Y%m%d'
    fmt_lang = '%Y-%m-%d %H:%M:%S'

    # Ausgabe im Befehlsfenster
    kanal = stdout if typ.value < MeldeTyp.FEHLER.value else stderr

    proto_meld = 'unbekannt'
    if typ == MeldeTyp.DEBUG:
        proto_meld = 'Debug:'
    if typ == MeldeTyp.INFO:
        proto_meld = 'Info:'
    elif typ == MeldeTyp.WARN:
        proto_meld = '!Warnung!'
    elif typ == MeldeTyp.FEHLER:
        proto_meld = '* FEHLER *'
    elif typ == MeldeTyp.FATAL:
        proto_meld = '\n  ** F A T A L ** '
    elif typ == MeldeTyp.IMMER:
        proto_meld = 'Standard:'

    # Text bereiten und ggf. am Bildschirm ausgeben
    proto_text = f'{time.strftime(fmt_lang)}. {proto_meld} {text}'
    if typ.value >= _print_grad:
        print(proto_text, file=kanal)

    # Ausgabe ins Protokoll?
    if typ.value < _proto_grad:
        return

    # also Protokoll führen
    proto_datei = _DATEI_PROTO_NAME + time.strftime(fmt_kurz) + _DATEI_PROTO_EXT

    # Neuen Eintrag schreiben
    with codecs.open(proto_datei, 'a', 'utf-8') as pf:
        pf.write(proto_text + '\n')

# ------------------------------------------------------------- Ende Gelände #

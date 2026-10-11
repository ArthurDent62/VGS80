"""
Gemeinsame Elemente für Prüfung und Simulation.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-04 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from enum import Enum, auto, unique

# -------------------------------------------------------------------------- #
@unique
class TastenTyp(Enum):
    """Zur einfacheren Abarbeitung der Tasten werden diese Typen zugeordnet.
    Spätere Definition bedeutet höhere Wichtigkeit = Typ.
    """
    # pylint: disable=bad-whitespace
    # erhöht hier die Lesbarkeit
    NIX      = 0       # keine-Taste-Typ
    WEICHE   = auto()  # Weichentaste
    VERSCHUB = auto()  # Verschubsignal
    VORSIG   = auto()  # Vorsignal
    ES       = auto()  # Einfahrsignal
    AS       = auto()  # Ausfahrsignal
    AS_LANG  = auto()  # Lange Einfahrt (AS als Ziel)
    STRECKE  = auto()  # Streckentaste
    GRUPPE   = auto()  # Gruppentaste
    DOKU     = auto()  # dokumentationspflichtig

    # pylint: disable=comparison-with-callable
    # unterdrücken der falschen Warnung beim Zugriff auf value
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

# ------------------------------------------------------------- Ende Gelände #

"""
Repräsentation verschiedener Melder.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-03-16 wh Datei mit Klasse VGrM begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from c_basis import ABC_VGS80Element
from m_pult_ausgabe import schalte_led as sled
from m_ausgaben import MeldeTyp as MTyp, melde

# Konstante

# -------------------------------------------------------------------------- #
class VGrM(ABC_VGS80Element):
    """Die Repräsentation eines Verschubsignalgrundstellungsmelders.
    """

    def __init__(self, t_name, led_kanal):
        """Initialisierung des VGr Melders und seiner Daten.
        :param  t_name     str   Name des Melders
        :param  led_kanal  int   Kanal der LED
        """
        super().__init__(t_name)

        # kanal der led merken
        self.__led = led_kanal

        # Zustand des VGrM initialisieren
        self._aufgehobene = set()
        sled(self.__led, True)

    # ---------------------------------------------------------------------- #
    def verschub_bei(self, signal, aufgehoben):
        """Informiert uns, dass ein Verschubsignal (am Ausfahrsignal) auf
        geändert wurde.
        :param  signal      str    Name des Signals
        :param  aufgehoben  bool   True=Verschubverbot aufgehoben
        """
        if aufgehoben:
            # VV wurde aufgehoben, Signal vermerken
            self._aufgehobene.add(signal)
        else:
            # VV wieder in Kraft
            try:
                self._aufgehobene.remove(signal)
            except KeyError:
                # es kann vorkommen dass verschub bereits verboten war
                pass

        # Melder aktualisieren
        sled(self.__led, not self._aufgehobene)

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Teil des Eltern-Klasse, aber für Melder nicht relevant.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        melde(MTyp.WARN, \
              f'kein Tastenaufruf ({taste}) vorgesehen für Melder ' + self._tname)

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Melders am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, \
              f'VGrM: {self._tname}:  aufgehoben sind ' + \
              f'{[str(e) for e in self._aufgehobene]}')

# ------------------------------------------------------------- Ende Gelände #

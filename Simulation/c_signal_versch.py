"""
Repräsentation eines VerschubSignals.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-03-05 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
#
# Anmerkungen:
# Obwohl ein Verschubsignal keinen Verschlußmelder hat, bleibt es doch laut
# Sperrenliste verschlossen, wenn eine entsprechende Fahrstraße gestellt ist.
# -------------------------------------------------------------------------- #

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Element, SigZustand as SZus
from m_pult_ausgabe import schalte_led as sled

# -------------------------------------------------------------------------- #
class VerschubSignal(ABC_VGS80Element):
    """Die Repräsentation eines Verschubsignals.
    """

    def __init__(self, t_name, led_liste):
        """Initialisierung des Verschubsignals und seiner Daten.
        :param  t_name     str   Name der Signaltaste
        :param  led_liste (int)  Kanäle der LEDs
        """
        super().__init__(t_name)

        # kanal jeder led merken
        self.__led_verbot, self.__led_aufgehoben = led_liste

        # Zustand des Signals initialisieren
        sled(self.__led_verbot, True)
        sled(self.__led_aufgehoben, False)

        # weitere inits
        self.__fahrstr_verschl = set()  # eingelaufene Fahrstraßen die uns verschließen

    # ---------------------------------------------------------------------- #
    def verschluss(self, fahrstrasse):
        """Verschließt wenn möglich das Signal.
        :param  fahrstrasse obj   Fahrstrasse
        :return False   wenn Verschubverbot derzeit aufgehoben
        """

        if self._zustand & SZus.AUFGEHOBEN:
            melde(MTyp.WARN, \
                  f'kein Verschluß für Verschubsignal {self._tname} da aufgehoben')
            return False

        # also verschließen = Fahrstraße zur Liste der verschließenden hinzufügen
        self.__fahrstr_verschl.add(fahrstrasse)
        return True

    # ---------------------------------------------------------------------- #
    def aufschluss(self, fahrstrasse):
        """Löst den Verschluß durch die benannte Fahrstraße.
        :param  fahrstrasse obj   Fahrstrasse
        """
        try:
            self.__fahrstr_verschl.remove(fahrstrasse)
        except KeyError:
            pass        # hier könnte auch ihre Fehlermeldung stehen

    # ---------------------------------------------------------------------- #
    def _aufheben(self):
        """Aufheben des Verschubverbots. §21 (3) (4)
        """
        if self.__fahrstr_verschl:
            melde(MTyp.WARN, f'{self} ' + \
                  'Verschubverbot aufheben nicht möglich da verschlossen ' + \
                  f'durch: {[str(e) for e in self.__fahrstr_verschl]}')
            return

        self._zustand |= SZus.AUFGEHOBEN
        sled(self.__led_verbot, False)
        sled(self.__led_aufgehoben, True)

    # ---------------------------------------------------------------------- #
    def verbieten(self):
        """Verschubverbot schalten. §22 (3), auch §21 (4) relevant
        """
        self._zustand &= ~SZus.AUFGEHOBEN       # pylint: disable=invalid-unary-operand-type
                                                # er weiss es halt nicht besser :-(
        sled(self.__led_verbot, True)
        sled(self.__led_aufgehoben, False)

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.VGT:      # Verschub-Gruppentaste
            self._aufheben()
        elif taste == Taste.HaGT:   # Halt-Gruppentaste
            self.verbieten()

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Signals am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, f'Verschubsignal: {self._tname}:  ' \
                + ('VV aufge; ' if self._zustand & SZus.AUFGEHOBEN else 'V.Verbot; ') \
                + f' FahrstrListe: {[str(e) for e in self.__fahrstr_verschl]}')

# ------------------------------------------------------------- Ende Gelände #

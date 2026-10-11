"""
Repräsentation eines Pseudosignals für die Ausfahrt auf die Strecke.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-03-06 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# TODO_Phase3: Ausfahrt speichern und Speichermelder aktivieren
# -------------------------------------------------------------------------- #

from daten_basis import Taste
from m_ausgaben import melde
from c_basis import ABC_VGS80Fahrstrassenziel, SigZustand as SZus
from m_pult_ausgabe import schalte_led as sled

# -------------------------------------------------------------------------- #
class Strecke(ABC_VGS80Fahrstrassenziel):
    """Die Repräsentation eines Pseudosignals für die Ausfahrt auf die Strecke.
    """

    def __init__(self, t_name, led_liste):
        """Initialisierung des Pseudo-Streckensignals und seiner Daten.
        :param  t_name     str   Name der Streckentaste
        :param  led_liste (int)  Kanäle der LEDs
        """
        super().__init__(t_name)

        # kanal jeder led merken
        self.__led_speicher, self.__led_sperr = led_liste

        # Zustand des Signals initialisieren
        sled(self.__led_speicher, False)
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def _sperren(self):
        """Sperrt die Ausfahrt gemäß §23 (2) (6)
        """
        self._zustand |= SZus.SPERR
        sled(self.__led_sperr, True)

    # ---------------------------------------------------------------------- #
    def _entsperren(self):
        """Entsperrt das Vorsignal gemäß §23 (3) (6)
        """
        self._zustand &= ~SZus.SPERR    # pylint: disable=invalid-unary-operand-type
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.SpT:        # Sperren
            self._sperren()
        elif taste == Taste.EspT:     # Entsperren
            self._entsperren()
        elif taste == Taste.FHT:      # Fahrstrassen-Hilfsauflösung
            if self._bin_ziel_der_fahrstr is not None:
                self._bin_ziel_der_fahrstr.aufloesen()

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Pseudosignals am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
                # TODO_Phase3 ('Speicher; ' if self._zustand & SZus.SPEICHER else 'keine; ') + \
        melde(melde_typ, f'Strecke: {self._tname}:  Ausfahrt ' + \
                ('gesperr; ' if self._zustand & SZus.SPERR else 'n.sperr; ') + \
                f'Fahrstrassenziel von {self._bin_ziel_der_fahrstr}')

# ------------------------------------------------------------- Ende Gelände #

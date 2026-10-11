"""
Repräsentation eines Einfahrsignals.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-03-07 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Hauptsignal, ABC_VGS80Vorsignal, SigZustand as SZus
import m_basis
from m_pult_ausgabe import schalte_led as sled
from m_common import TastenTyp

# -------------------------------------------------------------------------- #
# pylint: disable=too-many-instance-attributes
# So viele LEDs zu verwalten und weitere Daten!
class EinfahrSignal(ABC_VGS80Vorsignal, ABC_VGS80Hauptsignal):
    """Die Repräsentation eines Einfahrsignals in den Bahnhof.
    """

    def __init__(self, t_name, led_liste, vs_name):
        """Initialisierung des Einfahrsignals und seiner Daten.
        :param  t_name     str   Name der Signaltaste
        :param  led_liste (int)  Kanäle der LEDs
        :param  vs_name    str   Name des zugehörigen Vorsignals
        """

        # kanal jeder led merken
        self.__led_hs_gruen, self.__led_rot, self.__led_weiss, self.__led_orange, \
                self.__led_vs_gruen, led_fahrstra = led_liste

        # init Basisklasse ..start
        super().__init__(t_name, led_fahrstra)

        self.__vorsignal = m_basis.elemente[Taste[vs_name]]        # Vorsignal zuordnen

        # LEDs
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def _signalbild_herstellen(self):
        """Aktualisiert das Signalbild am Pult entsprechend dem Zustand.
        Implementierung.
        """
        if self._zustand & SZus.HS_FREI:
            sled(self.__led_rot, False)
            sled(self.__led_weiss, False)
            sled(self.__led_hs_gruen, True)

            # Zustand des AS anzeigen
            frei_ist = self._zustand & SZus.VS_GRUEN
            sled(self.__led_vs_gruen, frei_ist)
            sled(self.__led_orange, not frei_ist)

            self.__vorsignal.hs_ist_frei()  # Vorsignal informieren

        else:   # ES ist nicht frei
            sled(self.__led_hs_gruen, False)
            frei_ist = self._zustand & SZus.ERSATZ
            sled(self.__led_weiss, frei_ist)
            sled(self.__led_rot, not frei_ist)

            # AVS ist dann finster
            sled(self.__led_vs_gruen, False)
            sled(self.__led_orange, False)

            self.__vorsignal.hs_ist_halt()  # Vorsignal informieren

    # ---------------------------------------------------------------------- #
    def haltstellen(self):
        """Stellt das Signal auf -HALT- nach §22.
        Auch als externer Einsprungpunkt von der Signalzugschlussstelle.
        Implementierung.
        """
        # pylint: disable=invalid-unary-operand-type
        # er weiss es halt nicht besser :-(
        self._zustand &= ~SZus.HS_FREI      # Nach §22 (1)(2)
        self._zustand &= ~SZus.ERSATZ       # Nach §22 (4)a,b
#         self._zustand &= ~SZus.VS_GRUEN     # nicht notwendig, zur Sicherheit
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def hs_ist_frei(self):
        """Ein zugeordnetes Hauptsignal ist -FREI- geworden.
        Implementierung.
        """
        self._zustand |= SZus.VS_GRUEN
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def hs_ist_halt(self):
        """Ein zugeordnetes Hauptsignal ist auf -HALT- gefallen.
        Implementierung.
        """
        self._zustand &= ~SZus.VS_GRUEN   # pylint: disable=invalid-unary-operand-type
                                                        # weiss es halt nicht besser
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        # erst mal den Papa machen lassen
        if ABC_VGS80Hauptsignal.verarbeite(self, taste):
            return

        if taste.typ in {TastenTyp.AS, TastenTyp.AS_LANG}:
            # besser warnen: für die beiden Tasten gibt es keine Fahrstrasse
            melde(MTyp.WARN, 'Keine Definition einer Fahrstrasse von ' + \
                      f'{self._tname} nach {taste.name} gefunden !')

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Signals am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, f'ES: {self._tname}: VS={self.__vorsignal}:  ' \
                + ('-FREI-; ' if self._zustand & SZus.HS_FREI else '-HALT-; ') \
                + ('-HS FREI-;  ' if self._zustand & SZus.VS_GRUEN else '-VORSICHT-; ') \
                + ('Ersatz=An;  ' if self._zustand & SZus.ERSATZ else 'Ersatz=Aus; ') \
                + ('FS-ÜM=1; ' if self._fsuem_an else 'FS-ÜM=0; '))

# ------------------------------------------------------------- Ende Gelände #

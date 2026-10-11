"""
Repräsentation eines Einfahr-Vorsignals.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-03-05 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Vorsignal, SigZustand as SZus
from m_pult_ausgabe import schalte_led as sled

# Konstante

# -------------------------------------------------------------------------- #
class EinfahrVorsignal(ABC_VGS80Vorsignal):
    """Die Repräsentation eines EinfahrVorsignals.
    """

    def __init__(self, t_name, led_liste):
        """Initialisierung des Einfahr-Vorsignals und seiner Daten.
        :param  t_name     str   Name der Signaltaste
        :param  led_liste (int)  Kanäle der LEDs
        """
        super().__init__(t_name)

        # kanal jeder led merken
        self.__led_orange, self.__led_gruen, self.__led_sperr = led_liste

        # Zustand des EVS initialisieren
        self._zeige_frei(False)
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def _zeige_frei(self, ist_frei):
        """Setzt das Signalbild am Pult entsprechend dem Parameter.
        :param  ist_frei  bool  True=zeige -HAUPTSIGNAL FREI-
        """
        sled(self.__led_orange, not ist_frei)
        sled(self.__led_gruen, ist_frei)

    # ---------------------------------------------------------------------- #
    def _sperren(self):
        """Sperrt das Vorsignal gemäß §23 (1) (2) (7)
        """
        if self._zustand & SZus.VS_GRUEN:
            melde(MTyp.WARN, 'kann grünes VS nicht sperren!')
            return

        self._zustand |= SZus.SPERR
        sled(self.__led_sperr, True)

    # ---------------------------------------------------------------------- #
    def _entsperren(self):
        """Entsperrt das Vorsignal gemäß §23 (1) (3) (7)
        """
        self._zustand &= ~SZus.SPERR    # pylint: disable=invalid-unary-operand-type
        sled(self.__led_sperr, False)

        # ggf. Signalbild aktualisieren
        self._zeige_frei(self._zustand & SZus.VS_GRUEN)

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.SpT:      # Sperren
            self._sperren()
        elif taste == Taste.EspT:   # Entsperren
            self._entsperren()

    # ---------------------------------------------------------------------- #
    def hs_ist_frei(self):
        """Unser zugeordnetes Hauptsignal ist -FREI-.
        Implementierung.
        """
        self._zustand |= SZus.VS_GRUEN
        self._zeige_frei(not self._zustand & SZus.SPERR)

    # ---------------------------------------------------------------------- #
    def hs_ist_halt(self):
        """Unser zugeordnetes Hauptsignal ist auf -HALT-.
        Implementierung.
        """
        if self._zustand & SZus.VS_GRUEN:
            # eine Entsperrung des EVS erfolgt automatisch bei Auflösen der Zugstraße
            # §23 (7)
            # Voraussetzung: ES war vorher -FREI-, erkennbar am aktuellen VS_GRUEN
            self._entsperren()

        self._zustand &= ~SZus.VS_GRUEN # pylint: disable=invalid-unary-operand-type
        self._zeige_frei(False)

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Signals am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, f'EVS: {self._tname}:  Zustand=' \
                + ('VS_GRÜN; ' if self._zustand & SZus.VS_GRUEN else 'orange; ') \
                + ('gesperrt; ' if self._zustand & SZus.SPERR else 'n.sperr; '))

# ------------------------------------------------------------- Ende Gelände #

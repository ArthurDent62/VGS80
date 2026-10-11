"""
Repräsentation eines Ausfahrsignals.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-03-13 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Hauptsignal, ABC_VGS80Fahrstrassenziel, SigZustand as SZus
import m_basis          # einzeln importierte Variablen werden nicht aktualisiert!
from m_pult_ausgabe import schalte_led as sled
from m_common import TastenTyp

# -------------------------------------------------------------------------- #
# pylint: disable=too-many-instance-attributes
# So viele LEDs zu verwalten und weitere Daten!
class Ausfahr_VerschubSignal(ABC_VGS80Hauptsignal, ABC_VGS80Fahrstrassenziel):
    """Die Repräsentation eines Ausfahrsignals in den Bahnhof.
    """

    def __init__(self, t_name, led_liste, vgrm_name):
        """Initialisierung des Ausfahrsignals und seiner Daten.
        :param  t_name     str   Name der Signaltaste
        :param  led_liste (int)  Kanäle der LEDs
        :param  vgrm_name  str   Name des zugehörigen VerschubsignalGrMelder
        """

        # kanal jeder led merken
        self.__led_hs_gruen, self.__led_weiss, self.__led_rot, \
                self.__led_aufgehoben, led_fahrstra, \
                self.__led_sperr = led_liste

        # init von ..start
        super().__init__(t_name, led_fahrstra)

        # benötigte Elemente zuordnen, Daten initialisieren
        self.__vgrm = m_basis.elemente[vgrm_name]       # VGrM haben keine Taste, daher str
        self.vs_setzen()

        # LEDs
        self._signalbild_herstellen()

        # weitere inits
        self.__fahrstr_verschl = set()  # eingelaufene Fahrstraßen die uns verschließen

    # ---------------------------------------------------------------------- #
    def _signalbild_herstellen(self):
        """Aktualisiert das Signalbild am Pult entsprechend dem Zustand.
        Implementierung.
        """
        if self._zustand & SZus.HS_FREI:
            if self.__vorsignal is not None:
                self.__vorsignal.hs_ist_frei()  # Vorsignal informieren
            sled(self.__led_rot, False)
            sled(self.__led_weiss, False)
            sled(self.__led_hs_gruen, True)

        else:
            if self.__vorsignal is not None:
                self.__vorsignal.hs_ist_halt()  # Vorsignal informieren
            sled(self.__led_hs_gruen, False)
            ersatz_ein = self._zustand & SZus.ERSATZ
            sled(self.__led_weiss, ersatz_ein)
            sled(self.__led_rot, not ersatz_ein)

    # ---------------------------------------------------------------------- #
    def haltstellen(self):
        """Stellt das Signal auf -HALT- nach §22.
        Auch als externer Einsprungpunkt von der Signalzugschlussstelle. (1)&(4)
        Implementierung.
        """
        # pylint: disable=invalid-unary-operand-type
        # pylint kann ~ nicht auf auto() anwenden
        self._zustand &= ~SZus.HS_FREI        # Nach §22 (1)(2)
        self._zustand &= ~SZus.AUFGEHOBEN     # Nach §22 (3)
        self._zustand &= ~SZus.ERSATZ         # Nach §22 (4)a,b
        self._signalbild_herstellen()
        self.__vgrm.verschub_bei(self._tname, False)
        sled(self.__led_aufgehoben, False)

    # ---------------------------------------------------------------------- #
    def verschluss(self, fahrstrasse):
        """Verschließt wenn möglich das Signal.
        :param  fahrstrasse obj   Fahrstrasse
        :return False   wenn Verschubverbot derzeit aufgehoben
        """
        # Es wird nur auf das Verschubsignal geprüft, die Anzeige "FREI" wird
        # durch den Fahrstraßenausschluss verhindert
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
        Nicht möglich bei Fahrstraßenverschluss. §16 (2) 2.Absatz
        Jedoch Einzelsperrung wirkt _nicht_ auf Verschub! §23 (6)
        """
        if self.__fahrstr_verschl:
            melde(MTyp.WARN, f'{self} ' + \
                  'Verschubverbot aufheben nicht möglich da verschlossen ' + \
                  f'durch: {[str(e) for e in self.__fahrstr_verschl]}')
            return

        self._zustand |= SZus.AUFGEHOBEN
        self.__vgrm.verschub_bei(self._tname, True)
        sled(self.__led_aufgehoben, True)

    # ---------------------------------------------------------------------- #
    def _sperren(self):
        """Sperrt das Signal gemäß §23 (2) (6)
        """
        self._zustand |= SZus.SPERR
        sled(self.__led_sperr, True)

    # ---------------------------------------------------------------------- #
    def _entsperren(self):
        """Entsperrt das Signal gemäß §23 (3) (6)
        """
        self._zustand &= ~SZus.SPERR    # pylint: disable=invalid-unary-operand-type
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def vs_setzen(self, vs=None):
        """Setzen oder löschen des zugeordneten Vorsignals. Dieses kann von der
        eingelaufenen Zugstrasse abhängig sein und wird daher von der Fs
        gesetzt und gelöscht.
        :param vs  obj  Objekt-Repräsentation des Vorsignals
        """
        self.__vorsignal = vs

        # aktuellen Zustand an das Vorsignal senden
        if vs is not None:
            if self._zustand & SZus.HS_FREI:
                vs.hs_ist_frei()
            else:
                vs.hs_ist_halt()

    # ---------------------------------------------------------------------- #
    def kein_ziel(self, fahrstrasse):
        """Wir sind kein Fahrstrassenziel mehr.
        Override.
        :param  fahrstrasse obj   die auflösende Fahrstrasse
        """
        super().kein_ziel(fahrstrasse)

        # wenn kein Fehler aufgetreten ist, dann ist das Ziel nun gelöscht
        if self._bin_ziel_der_fahrstr is None:
            self.vs_setzen()            # dann auch das Vorsignal löschen

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param taste  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.VGT:          # Verschub-Gruppentaste
            self._aufheben()
        elif taste == Taste.SpT:        # sperren
            self._sperren()
        elif taste == Taste.EspT:       # entsperren
            self._entsperren()
        elif taste == Taste.FHT:        # Fahrstrassen-Hilfsauflösung
            if self._bin_ziel_der_fahrstr is not None:
                self._bin_ziel_der_fahrstr.aufloesen()

        # vielleicht können die Eltern da was tun?
        elif ABC_VGS80Hauptsignal.verarbeite(self, taste):
            pass            # wenn verarbeitet, dann ist gut

        elif taste.typ == TastenTyp.STRECKE:
            # besser warnen: für die beiden Tasten gibt es keine Fahrstrasse
            melde(MTyp.WARN, 'Keine Definition einer Fahrstrasse von ' + \
                      f'{self._tname} nach {taste.name} gefunden !')

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status des Signals am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, f'AS: {self._tname}: VS={self.__vorsignal}:  ' \
                + ('-FREI-; ' if self._zustand & SZus.HS_FREI else '-HALT-; ') \
                + ('VV aufge; ' if self._zustand & SZus.AUFGEHOBEN else 'V.Verbot; ') \
                + ('Ersatz=An;  ' if self._zustand & SZus.ERSATZ else 'Ersatz=Aus; ') \
                + ('gesperr; ' if self._zustand & SZus.SPERR else 'n.sperr; ') \
                + ('FS-ÜM=1; ' if self._fsuem_an else 'FS-ÜM=0; ') \
                + f'Fahrstrassenziel von {self._bin_ziel_der_fahrstr}' \
                + f' FahrstrListe: {[str(e) for e in self.__fahrstr_verschl]}')

# ------------------------------------------------------------- Ende Gelände #

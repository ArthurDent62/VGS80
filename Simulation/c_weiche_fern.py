"""
Klasse für fernbediente Weichen.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-09 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
#
# ZUKUNFT: Umstellen der Weichen-Umstell-Blinker sodass während dem Blinken
#   sich belegt=rot/frei=weiß ändern kann. Auch das Auffahren einer Weiche mit
#   Blinken beider Fahrwege ist derzeit nicht direkt, synchronisiert möglich.
#   Idee: call_back welches bei jedem True die Kanäle zurückliefert (bei False
#   müssen natürlich die aktuellen Kanäle wieder abgeschalten werden!)
# -------------------------------------------------------------------------- #

from enum import Flag, auto

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Element
from m_pult_ausgabe import schalte_led as sled, blinken_start as blein, \
        blinken_stop_regular as blaus

# Konstante
_BL_UMSTELL = 5     # Anzahl der Blinkwechsel beim Umstellen
_NAME_RE = '_re'    # Blinker Name Ergänzung Stellung nach rechts
_NAME_LI = '_li'    # Blinker Name Ergänzung Stellung nach links
_NAME_NAH = '_nah'  # Blinker Name Ergänzung zur Nahbedienung frei

# -------------------------------------------------------------------------- #
class WZustand(Flag):
    """Darstellung des aktuellen Zustands einer Weiche.
    """
    INIT = 0            # kein Flag gesetzt
    LINKS = auto()      # 0 = rechts
    BELEGT = auto()     # da steht grad ein Schienenfahrzeug drauf
    VERSCHL = auto()    # verschlossen
    SPERR = auto()      # gesperrt
    NAH = auto()        # zur Nahbedienung freigegeben
    UMSTELL = auto()    # läuft gerade um

# -------------------------------------------------------------------------- #
class FernWeiche(ABC_VGS80Element):
    """Die Repräsentation einer fernbedienten Weiche.
    """
    # pylint: disable= too-many-instance-attributes
    # Hier brauchts halt diese vielen unterschiedlichen Attribute

    def __init__(self, t_name, led_liste, is_links=False):
        """Initialisierung einer neuen Weiche und ihrer Daten.
        :param  t_name   string  Name der Weichentaste
        :param  led_liste (int)  Kanal für alle LEDs
        :param  is_links bool    True wenn die Weiche mit links initialisiert werden soll
        """
        super().__init__(t_name)

        # leds merken
        self.__led_versch, self.__led_sperr, self.__led_reFrei, \
                self.__led_reBel, self.__led_liFrei, self.__led_liBel = led_liste

        # Zustand der Weiche initialisieren
        self.__zustand = WZustand.INIT
        if is_links:
            self.__zustand |= WZustand.LINKS
            sled(self.__led_liFrei, True)
        else:
            sled(self.__led_reFrei, True)

        # weitere inits
        self.__fahrstr_verschl = set()

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für die Weiche gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.WGT:      # Weichengruppe
            self._umstellen()
        elif taste == Taste.NFT:    # Nahstellbetrieb Freigabe
            self._nah_frei_nach_pruef()
        elif taste == Taste.NHT:    # Nahstellbetrieb Hilfsrücknahme
            self._nah_rueck()
        elif taste == Taste.SpT:    # Sperr
            self._sperren()
        elif taste == Taste.EspT:   # Entsperr
            self._entsperren()

    # ---------------------------------------------------------------------- #
    def _cb_umst_fertig(self):
        """Umstellen der Weiche beendet.
        """
        be = self.__zustand & WZustand.BELEGT

        if self.__zustand & WZustand.LINKS:
            sled(self.__led_liBel if be else self.__led_liFrei, True)
        else:
            sled(self.__led_reBel if be else self.__led_reFrei, True)

        self.__zustand &= ~WZustand.UMSTELL     # pylint: disable=invalid-unary-operand-type

    # ---------------------------------------------------------------------- #
    def _umstellen(self):
        """Umstellen der Weiche.
        """
        # pylint: disable=invalid-name

        # prüfen ob Umstellen möglich ist §13 (2)
        if self.__zustand & (WZustand.VERSCHL \
                | WZustand.SPERR | WZustand.NAH | WZustand.UMSTELL):
            return      # nicht möglich

        self.__zustand |= WZustand.UMSTELL
        be = self.__zustand & WZustand.BELEGT

        if self.__zustand & WZustand.LINKS:
            # nach rechts umstellen
            self.__zustand &= ~WZustand.LINKS   # pylint: disable=invalid-unary-operand-type
            sled(self.__led_liFrei, False)
            sled(self.__led_liBel, False)
            blein(self._tname + _NAME_RE, self.__led_reBel if be else self.__led_reFrei, \
                    _BL_UMSTELL, cb_ende=self._cb_umst_fertig)
        else:
            # nach links umstellen
            self.__zustand |= WZustand.LINKS
            sled(self.__led_reFrei, False)
            sled(self.__led_reBel, False)
            blein(self._tname + _NAME_LI, self.__led_liBel if be else self.__led_liFrei, \
                    _BL_UMSTELL, cb_ende=self._cb_umst_fertig)

    # ---------------------------------------------------------------------- #
    def _nah_rueck(self):
        """Nimmt die Freigabe zur Nahbedienung zurück.
        """
        # siehe §13 (5-6)
        self.__zustand &= ~WZustand.NAH     # pylint: disable=invalid-unary-operand-type

        # Nahbedienung und Sperren verwenden die gleiche LED
        if not self.__zustand & WZustand.SPERR:
            # nur wenn nicht gesperrt dann gibts einen Blinker zu stoppen
            # ... und darf die LED ausgeschalten werden
            blaus(self._tname + _NAME_NAH)
            sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def _nah_frei_nach_pruef(self):
        """Setzt (wenn möglich) den Zustand auf "zur Nahbedienung freigegeben".
        """
        # Ob Änderung möglich siehe §13 (3); nicht wenn bereits nahbedient
        if self.__zustand & (WZustand.VERSCHL | WZustand.SPERR | WZustand.NAH):
            return

        self._nah_frei_tun()

    # ---------------------------------------------------------------------- #
    def _nah_frei_tun(self):
        """Setzt (ohne Prüfung) den Zustand auf "zur Nahbedienung freigegeben".
        """
        self.__zustand |= WZustand.NAH
        blein(self._tname + _NAME_NAH, self.__led_sperr, -1)

    # ---------------------------------------------------------------------- #
    def _sperren(self):
        """Sperren der Weiche.
        """
        self.__zustand |= WZustand.SPERR

        if self.__zustand & WZustand.NAH:
            # laut §23 (4) möglich -> Blinker stoppen!
            blaus(self._tname + _NAME_NAH)
        sled(self.__led_sperr, True)

    # ---------------------------------------------------------------------- #
    def _entsperren(self):
        """Entsperren der Weiche.
        """
        self.__zustand &= ~WZustand.SPERR   # pylint: disable=invalid-unary-operand-type

        if self.__zustand & WZustand.NAH:
            # In §23 (4) ist nicht genau beschrieben was nach Entsperren einer
            # zuvor zur Nahbedienung freigegebenen fernbedienten Weiche geschieht;
            # laut Thomas Strassmayer besteht im realen Stellpult die
            # Nahbedienung danach wieder   (Email aus Nov/Dez. 2019)
            # -> also Blinker wieder starten
            self._nah_frei_tun()
        else:
            sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def verschluss(self, fahrstrasse, ist_links):
        """Verschließt wenn möglich die Weiche.
        :param  fahrstrasse obj   Fahrstrasse
        :param  ist_links  bool   notwendige Lage fürs verschließen
        :return False   wenn verschließen nicht möglich oder Lage falsch
        """
        m_txt = f'kein Verschluß für Weiche {self._tname} - '

        # siehe §16 (2)a
        if self.__zustand & WZustand.NAH:
            melde(MTyp.WARN, m_txt + 'Nahbedienung!')
            return False

        if self.__zustand & WZustand.UMSTELL:
            melde(MTyp.WARN, m_txt + 'in Umstellung')
            return False

        if ist_links and not self.__zustand & WZustand.LINKS:
            # Weiche steht nicht nach links
            melde(MTyp.WARN, m_txt + 'nicht nach links')
            return False

        if not ist_links and self.__zustand & WZustand.LINKS:
            # Weiche steht nicht nach rechts
            melde(MTyp.WARN, m_txt + 'nicht nach rechts')
            return False

        # also verschließen
        self.__zustand |= WZustand.VERSCHL
        # Fahrstraße zur Liste der verschließenden hinzufügen
        self.__fahrstr_verschl.add(fahrstrasse)
        # Verschlussmelder anschalten
        sled(self.__led_versch, True)

        return True

    # ---------------------------------------------------------------------- #
    def aufschluss(self, fahrstrasse):
        """Löst den Verschluß durch die benannte Fahrstraße.
        :param  fahrstrasse obj   Fahrstrasse
        """
        try:
            self.__fahrstr_verschl.remove(fahrstrasse)
        except KeyError:
            pass

        # Wenn keine Fahrstraße mehr die Weiche benötigt
        if not self.__fahrstr_verschl:
            # Verschlussmelder abschalten
            sled(self.__led_versch, False)
            # Zustand anpassen
            self.__zustand &= ~WZustand.VERSCHL     # pylint: disable=invalid-unary-operand-type

    # ---------------------------------------------------------------------- #
    def setz_belegt(self, belegt):
        """Setze den Status auf belegt oder frei.
        """
        if belegt:
            self.__zustand |= WZustand.BELEGT
            if self.__zustand & WZustand.LINKS:
                sled(self.__led_liFrei, False)
                sled(self.__led_liBel, True)
            else:
                sled(self.__led_reFrei, False)
                sled(self.__led_reBel, True)

        else:
            self.__zustand &= ~WZustand.BELEGT      # pylint: disable=invalid-unary-operand-type
            if self.__zustand & WZustand.LINKS:
                sled(self.__led_liBel, False)
                sled(self.__led_liFrei, True)
            else:
                sled(self.__led_reBel, False)
                sled(self.__led_reFrei, True)

    # ---------------------------------------------------------------------- #
    def show_status(self, melde_typ):
        """Zeigt den Status der Weiche am Bildschirm an (debug).
        Implementierung.
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldung
        """
        melde(melde_typ, f'Weiche: {self._tname}:  ' \
                + ('belegt; ' if self.__zustand & WZustand.BELEGT else 'frei;   ') \
                + ('verschl; ' if self.__zustand & WZustand.VERSCHL else 'n.v.;  ') \
                + ('sperr  ; ' if self.__zustand & WZustand.SPERR else 'n.sperr; ') \
                + ('nahbed; ' if self.__zustand & WZustand.NAH else 'ni.nah; ') \
                + ('links;  ' if self.__zustand & WZustand.LINKS else 'rechts; ') \
                + ('stellt; ' if self.__zustand & WZustand.UMSTELL else 'endlage;') \
                + f' FahrstrListe: {[str(e) for e in self.__fahrstr_verschl]}')

# ------------------------------------------------------------- Ende Gelände #

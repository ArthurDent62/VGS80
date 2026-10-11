"""
Klasse für ortsbediente Weichen (kombiniert mit Sperrschuh oder Schutzweiche).

Standardabfolge für Nahbedienung:
    a) Weichentaste WT_xx & Nahstellbetriebsfreigabetaste NFT:
        zustand = FREIGABE und ~ENTNAHME
    b1) Schlüssel wird entnommen:
        zustand = FREIGABE und ENTNAHME
    c) Schlüssel wird eingesperrt:
        zustand = ~FREIGABE und ~ENTNAHME
Alternativ:
    b2) WT_xx & Nahstellbetriebsrücknahmetaste NRT: direkt zu
        zustand = ~FREIGABE und ~ENTNAHME

Eine Hilfsrücknahme wie bei fernbedienten Weichen gibts bei ortsbedienten nicht!
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-24 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
#
# ZUKUNFT: Umstellen des Weichen-Blinker wenn sich während dem Blinken
#   die Belegung ändert (belegt=rot/frei=weiß). => setz_belegt()
#   Idee1: call_back welches bei jedem True die Kanäle zurückliefert (bei False
#       müssen natürlich die aktuellen Kanäle wieder abgeschalten werden!)
#       bedeutet Änderung des Timer-Konzepts!
#   Idee2: Wenn sich die Belegung ändert (frei<->belegt) ist zu prüfen ob grad
#       zur Nahbedienung freigegeben ist; in diesem Fall den Blinker stoppen und
#       mit geändertem led neu starten. bevorzugte Idee (04.12.2019)
# -------------------------------------------------------------------------- #

from enum import Flag, auto

from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from c_basis import ABC_VGS80Element
from m_pult_ausgabe import schalte_led as sled, blinken_start as blein, \
        blinken_stop_regular as blaus

# Konstante
_NAME_EGAL = '_'    # Blinker Name
_NAME_SCHLUE_DA = '_schlüssel_da'
_NAME_FREIGABE = '_freigabe'

# -------------------------------------------------------------------------- #
class WZustand(Flag):
    """Darstellung des aktuellen Zustands einer Weiche.
    """
    INIT = 0            # kein Flag gesetzt
    BELEGT = auto()     # da steht grad ein Schienenfahrzeug drauf
    VERSCHL = auto()    # verschlossen
    SPERR = auto()      # gesperrt
    FREIGABE = auto()   # Schlüssel freigegeben
    ENTNAHME = auto()   # Schlüssel entnommen

# -------------------------------------------------------------------------- #
class OrtsWeiche(ABC_VGS80Element):
    """Die Repräsentation einer ortsbedienten Weiche mit Sperrschuh oder
    Schutzweiche als zweitem Element in A/C oder A/B Abhängigkeit.
    """

    def __init__(self, t_name, led_liste):
        """Initialisierung einer neuen Weiche und ihrer Daten.
        :param  t_name  string   Name der Weichentaste
        :param  led_liste (int)  Kanal für alle LEDs
        """
        super().__init__(t_name)

        # leds merken
        self.__led_versch, self.__led_sperr, self.__led_frei, \
                self.__led_belegt, self.__led_schutz = led_liste

        # Zustand der Weiche initialisieren
        self.__zustand = WZustand.INIT
        self._grundstell()

        # weitere inits
        self.__fahrstr_verschl = set()

    # ---------------------------------------------------------------------- #
    # pylint: disable=invalid-unary-operand-type
    # ---------------------------------------------------------------------- #
    def schlue_weg(self):
        """Das ELF meldet die Entnahme des Schlüssels über diese Funktion.
        """
        self.__zustand |= WZustand.ENTNAHME

        # zur Sicherheit Fehlerzustände melden
        if self.__zustand & WZustand.SPERR:
            melde(MTyp.FEHLER, 'Schlüsselentnahme trotz Sperre bei ' + self._tname)
            return
        if self.__zustand & WZustand.VERSCHL:
            melde(MTyp.FEHLER, 'Schlüsselentnahme trotz Verschluss bei ' + self._tname)
            return

        # alles gut
        blaus(self._tname + _NAME_SCHLUE_DA)
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def schlue_da(self):
        """Das ELF meldet die Rückgabe des Schlüssels über diese Funktion.
        """
        self.__zustand &= ~WZustand.ENTNAHME
        self.__zustand &= ~WZustand.FREIGABE
        blaus(self._tname + _NAME_FREIGABE)
        self._grundstell()

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste): # TODO prüfen
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für die Weiche gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """
        if taste == Taste.NFT:      # Nahstellbetrieb Freigabe
            self._freigabe()
        elif taste == Taste.NRT:    # Nahstellbetrieb Rücknahme
            self._frei_rueck()
        elif taste == Taste.SpT:    # Sperren
            self._sperren()
        elif taste == Taste.EspT:   # Entsperren
            self._entsperren()

        # TODO Test-Tasten entfernen ++++++++++++++++++++++++++++++++++++++++
        elif taste == Taste.BGT:
            self.schlue_weg()
        elif taste == Taste.HaGT:
            self.schlue_da()
        elif taste == Taste.WUT:
            self.setz_belegt(True)
        elif taste == Taste.VGT:
            self.setz_belegt(False)

    # ---------------------------------------------------------------------- #
    def _led_frei_belegt(self):
        """Gibt die Kanalnummer der Weichen-LED aufgrund belegt/frei zurück.
        """
        return self.__led_belegt if self.__zustand & WZustand.BELEGT \
                        else self.__led_frei

    # ---------------------------------------------------------------------- #
    def _grundstell(self):
        """Setzt die LEDs in Grundstellung.
        """
        # erst löschen (zweite nicht, hat ja keine GFMA)
        sled(self.__led_frei, False)
        sled(self.__led_belegt, False)

        # dann neu setzen
        sled(self.__led_schutz, True)
        sled(self._led_frei_belegt(), True)

    # ---------------------------------------------------------------------- #
    def _frei_rueck(self):
        """Nimmt die Freigabe zur Nahbedienung am Pult zurück.
        """
        # Rücknahme nur bei Freigabe (somit nicht gesperrt oder verschlossen)
        if not self.__zustand & WZustand.FREIGABE:
            return

        # sofort das ELF blockieren
        #
        # ZUKUNFT: im Simulations-ELF Freigabe zurücknehmen
        # muss gegen gleichzeitige Änderung gesichert werden mit Semaphore
        # (Beispiel: m_pult_ausgabe)
        #
        # geht nicht bei abgezogenem Schlüssel, siehe §14 (5)
        if self.__zustand & WZustand.ENTNAHME:
            return

        # Freigabe zurücknehmen: Blinken stoppen, normale Anzeige
        self.__zustand &= ~WZustand.FREIGABE
        blaus(self._tname + _NAME_FREIGABE)
        blaus(self._tname + _NAME_SCHLUE_DA)
        sled(self.__led_sperr, False)
        self._grundstell()

    # ---------------------------------------------------------------------- #
    def _freigabe(self): # TODO prüfen: basicOK, verschl, sperrOK, entnommenOK, freiOK
        """Setzt (wenn möglich) den Zustand auf "Schlüssel im ELF freigegeben".
        """
        # Ob Änderung möglich siehe §14 (3); und: nicht wenn bereits entnommen
        # ... nicht wenn bereits freigegeben, sonst würde zusätzlicher Blinker starten
        if self.__zustand & (WZustand.VERSCHL | WZustand.SPERR \
                            | WZustand.ENTNAHME | WZustand.FREIGABE):
            return

        #
        # ZUKUNFT: im Simulations-ELF den Schlüssel freigeben
        #
        self.__zustand |= WZustand.FREIGABE
        blein(self._tname + _NAME_SCHLUE_DA, self.__led_sperr, -1)
        blein(self._tname + _NAME_FREIGABE, \
              (self._led_frei_belegt(), self.__led_schutz), -1)

    # ---------------------------------------------------------------------- #
    def _sperren(self):
        """Sperren der Weiche.
        """
        # sperren möglich?
        # laut §23 (5) nicht freigegeben (oder gar entnommen)
        if self.__zustand & (WZustand.FREIGABE | WZustand.ENTNAHME):
            return

        self.__zustand |= WZustand.SPERR
        sled(self.__led_sperr, True)

    # ---------------------------------------------------------------------- #
    def _entsperren(self):
        """Entsperren der Weiche.
        """
        self.__zustand &= ~WZustand.SPERR
        sled(self.__led_sperr, False)

    # ---------------------------------------------------------------------- #
    def verschluss(self, fahrstrasse, platzhalter): # pylint: disable=unused-argument
        """Verschließt wenn möglich die Weiche.
        :param  fahrstrasse obj   Fahrstrasse
        :param  platzhalter bool  hier ungenutzt (Stellung, nur bei Fernweiche)
        :return bool      False wenn verschließen nicht möglich
        """
        # siehe §16 (2)a
        if self.__zustand & (WZustand.FREIGABE | WZustand.ENTNAHME):
            melde(MTyp.INFO, 'Schlüssel freigegeben')
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
            self.__zustand &= ~WZustand.VERSCHL

    # ---------------------------------------------------------------------- #
    def setz_belegt(self, belegt):  # TODO prüfen basisOK, frei, entnahme
        """Setze den Status auf belegt oder frei.
        """
        if belegt:
            self.__zustand |= WZustand.BELEGT
        else:
            self.__zustand &= ~WZustand.BELEGT

        self._grundstell()

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
                + ('frei  ; ' if self.__zustand & WZustand.FREIGABE else 'ni.frei; ') \
                + ('entnom; ' if self.__zustand & WZustand.ENTNAHME else 'drin  ; ') \
                + f' FahrstrListe: {[str(e) for e in self.__fahrstr_verschl]}')

# ------------------------------------------------------------- Ende Gelände #

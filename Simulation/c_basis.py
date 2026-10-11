"""
Definition (abstrakter) Basis-Klassen.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-21 wh als Modul m_basis begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# 0.6 2020-02-08 wh Aufteilung wegen Problemen beim Import in m_basis und c_basis
# -------------------------------------------------------------------------- #

from enum import Flag, auto
from abc import ABC, abstractmethod

import m_basis
from daten_basis import Taste
from m_ausgaben import MeldeTyp as MTyp, melde
from m_pult_ausgabe import schalte_led as sled

# -------------------------------------------------- modulweite Definitionen #
# --- Konstante
_TXT_NO_ELEM_TASTE = 'keine Taste'

# -------------------------------------------------------------------------- #
class SigZustand(Flag):
    """Mögliche Zustände eines Signals.
    """
    # pylint: disable=bad-whitespace
    # Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht
    INIT       = 0         # kein Flag gesetzt
    HS_FREI    = auto()    # zeigt -FREI-
    VS_GRUEN   = auto()    # zeigt -HS FREI-
    AUFGEHOBEN = auto()    # zeigt -VERSCHUBVERBOT AUFGEHOBEN-
    ERSATZ     = auto()    # Ersatzsignal eingeschalten
    SPERR      = auto()    # gesperrt

# -------------------------------------------------------------------------- #
class FahrZustand(Flag):
    """Mögliche Zustände der Fahrstrasse.
    """
    # pylint: disable=bad-whitespace
    # Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht
    NICHT   = 0         # keine Fahrstrasse gestellt
    TEILS   = auto()    # teilweise eingelaufen, aber keine Fahrstrasse §16 (3)
    HILFS   = auto()    # Zughilfsstrasse gestellt
    ZUG     = auto()    # Zugstrasse gestellt

# -------------------------------------------------------------------------- #
class ABC_VGS80Element(ABC):
    """<i>Abstrakte</i> Basis-Klasse für alle Elemente, mit Implementierung von
    abstrakten Methoden als Rückfall-Ebene. Diese Methoden müssen von den
    Kind-Klassen implementiert werden.
    """

    # Konstruktor
    def __init__(self, taste_name=_TXT_NO_ELEM_TASTE):
        """Initialisierung eines neuen Elements mit allgemeinen Daten.
        :param  taste_name: str Bezeichnung der Taste des Elements
        """
        self._tname = taste_name
        # Jedes Element hat einen inneren Zustand, initialisiere hier
        self._zustand = SigZustand.INIT    # (geht auch wenn es kein Signal ist)

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def show_status(self, melde_typ):
        """Zeigt den Status des Elements am Bildschirm an (testen, Rückfall-Impl).
        :param melde_typ  MTyp  Ausgabe-Level der Status-Meldungen
        """

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Element gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        :param  taste:  Taste   zusätzlich gedrückte Taste
        """

    # ---------------------------------------------------------------------- #
    def __str__(self):
        """Liefert Bezeichnung des Elements zurück.
        """
        return f'<{self._tname}>'

    # ---------------------------------------------------------------------- #
    def taste_name(self):
        """Liefert den Namen der zugeordneten Taste zurück.
        """
        return self._tname

# -------------------------------------------------------------------------- #
class ABC_VGS80Vorsignal(ABC_VGS80Element):
    """<i>Abstrakte</i> Basis-Klasse für alle Elemente welche ein Signal mit
    einem Vorsignal implementieren. Definiert zusätzliche abstrakte Methoden
    eines Vorsignals.
    """

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def hs_ist_frei(self):
        """Unser zugeordnetes Hauptsignal ist -FREI- geworden.
        """

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def hs_ist_halt(self):
        """Unser zugeordnetes Hauptsignal ist auf -HALT- gefallen.
        """

# -------------------------------------------------------------------------- #
class ABC_VGS80Hauptsignal(ABC_VGS80Element):
    # pylint: disable=abstract-method
    # Zwischenklasse, erweitert abstrakte Klasse, nicht zum instantiieren gedacht
    """<i>Abstrakte</i> Basis-Klasse (aufgrund vererbter abstrakter Methoden)
    für alle Hauptsignale. Deklariert auch weitere abstrakte Methoden.
    """

    def __init__(self, t_name, led_fs):
        """Initialisierung eines Hauptsignals und seiner Daten.
        :param  t_name  str  Name der Signaltaste
        :param  led_fs  int  logischer LED-Kanal Fahrstrassen-Überwachungsmelder
        """
        super().__init__(t_name)        # init Elternteil

        # merken und initialisieren des FSÜM
        self._led_fsuem = led_fs
        self._fsuem_setzen(False)

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def _signalbild_herstellen(self):
        """Aktualisiert das Signalbild am Pult entsprechend dem inneren
        Signal-Zustand in {self._zustand}.
        """

    # ---------------------------------------------------------------------- #
    @abstractmethod
    def haltstellen(self):
        """Stellt das Signal auf -HALT- nach §22.
        Auch als externer Einsprungpunkt von der Signalzugschlussstelle. (1)&(4)
        """

    # ---------------------------------------------------------------------- #
    def _ersatz_ein(self):
        """Schaltet das -ERSATZSIGNAL-. §21 (5)
        Ausschalten über haltstellen(), oder automatisch. §22 (4)
        """
        if not m_basis.blinkspannung:
            # Ersatzsignal nur während Prüfung der Blinkspannung läuft
            melde(MTyp.WARN, \
                  f' {self._tname}: Ersatzsignal nur während BLÜM blinkt!')
            return

        if self._zustand & SigZustand.HS_FREI:
            # ist nach S54 nicht ausgeschlossen, aber sinnlos, daher nein
            melde(MTyp.WARN, \
                  f'{self._tname}: Ersatzsignal bei -FREI- sinnfrei!')
            return

        self._zustand |= SigZustand.ERSATZ
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def _fsuem_setzen(self, ein=True):
        """Schalten des Fahrstrassen-Überwachungsmelder.
        :param ein  bool  True schaltet den Melder ein, False aus
        """
        sled(self._led_fsuem, ein)       # Fs Überwachungsmelder schalten
        self._fsuem_an = ein

    # ---------------------------------------------------------------------- #
    def _zugstrasse_anzeigen(self, nach_name, fs_zustand):
        """Anzeigen einer Zugstrasse entsprechend ihres Status.
        :param nach_name   str   Bezeichnung des Zugstrassenziels
        :param fs_zustand  FahrZustand  Status der Fahrstrasse
        """
        melde(MTyp.DEBUG, f'Zugstrasse von {self._tname} nach {nach_name} '+ \
              f'hat Zustand {fs_zustand} erreicht!')

        # bei niedrigem Status ist nix zu tun
        # aber TODO_Phase3 Speichermelder Ausfahrt
        if fs_zustand in {FahrZustand.NICHT, FahrZustand.TEILS}:
            return

        # === Zughilfsstrasse ===
        self._fsuem_setzen()            # §17 (4)

        # === Zugstrasse ===
        if fs_zustand != FahrZustand.ZUG:
            return

        # pylint: disable=invalid-unary-operand-type
        # pylint kann ~ nicht auf auto() anwenden
        self._zustand &= ~SigZustand.ERSATZ
        self._zustand |= SigZustand.HS_FREI         # §16 (2)
        self._signalbild_herstellen()

    # ---------------------------------------------------------------------- #
    def zugstrasse_loeschen(self):
        """Der Zustand des AS wird angepasst, weil die beim AS beginnende
        Fahrstrasse aufgelöst wird.
        """
        self._fsuem_setzen(False)
        self.haltstellen()

    # ---------------------------------------------------------------------- #
    def verarbeite(self, taste):
        """Verarbeite die als Parameter übergebene Taste, welche gemeinsam mit
        der Taste für das Signal gedrückt wurde. Nicht sinnvolle Tasten werden
        ignoriert.
        Implementierung für gemeinsame Tasten aller Hauptsignale.
        :param  taste  Taste   zusätzlich gedrückte Taste
        :return True   wenn eine Taste verarbeitet wurde, sonst False
        """
        if taste == Taste.HaGT:       # Halt Stellen
            self.haltstellen()
        elif taste == Taste.ErsGT:    # Ersatzsignal
            self._ersatz_ein()

        else:
            try:
                fs = m_basis.fahrstrassen[self._tname, taste.name]
            except KeyError:
                # auch keine Fahrstrasse, also Taste ned verarbeitet
                return False

            # wenn fahrstrasse gefunden, stellen und anzeigen
            self._zugstrasse_anzeigen(taste.name, fs.stellen())

        # jedenfalls ist die 'taste' verarbeitet worden
        return True

# -------------------------------------------------------------------------- #
class ABC_VGS80Fahrstrassenziel(ABC_VGS80Element):
    # pylint: disable=abstract-method
    # Zwischenklasse, erweitert abstrakte Klasse, nicht zum instantiieren gedacht
    """<i>Abstrakte</i> Basis-Klasse (aufgrund vererbter abstrakter Methoden)
    für alle Signale, welche ein Fahrstrassenziel sein können.
    """

    def __init__(self, t_name):
        """Initialisierung eines Fahrstrassenziels und seiner Daten.
        :param  t_name     str   Name der Signaltaste
        """
        super().__init__(t_name)        # init Elternteil

        # um für die FHT gerüstet zu sein müssen wir die Fahrstrasse kennen
        self._bin_ziel_der_fahrstr = None

    # ---------------------------------------------------------------------- #
    def wird_ziel(self, fahrstrasse):
        """Wir werden ein Fahrstrassenziel.
        :param  fahrstrasse obj   Fahrstrasse deren Ziel wir sind
        :returns    True wenn alles gut
        """
        if self._zustand & SigZustand.SPERR:
            melde(MTyp.WARN, f'keine Fahrstrasse da Ziel {self._tname} gesperrt!')
            return False

        if self._bin_ziel_der_fahrstr:
            melde(MTyp.WARN, f'{self._tname} ist bereits ein Fahrstrassenziel!')
            return False

        self._bin_ziel_der_fahrstr = fahrstrasse
        return True

    # ---------------------------------------------------------------------- #
    def kein_ziel(self, fahrstrasse):
        """Wir sind kein Fahrstrassenziel mehr.
        :param  fahrstrasse obj   die auflösende Fahrstrasse
        """
        if self._bin_ziel_der_fahrstr == fahrstrasse:
            self._bin_ziel_der_fahrstr = None
        else:
            # da wollte jemand die Fahrstrasse auflösen der sie nicht stellte!
            melde(MTyp.FATAL, f'{fahrstrasse} wollte die durch ' \
                  f'{self._bin_ziel_der_fahrstr} gestellte Fahrstrasse auflösen')

# -------------------------------------------------------------------------- #
class ABC_VGS80PultAusgabeHW(ABC):
    """<i>Abstrakte</i> Basis-Klasse für Platinen, welche die Ansteuerung der
    LED des Pultes übernehmen. Die hier definierten, abstrakten Methoden müssen
    von einer Kind-Klasse spezifisch für die Platine implementiert werden.
    """

    @abstractmethod
    def __init__(self, max_kanal):
        """Initialisierung der Hardware.
        :param max_kanal  int  höchste benötigte Kanalnummer einer LED (0 - basiert)
        """
        melde(MTyp.DEBUG, 'Wurde abstraktes __init__ in AusgabeHardware implementiert?')

    @abstractmethod
    def helligkeit(self, mehr):
        """Verändert die Helligkeit um eine Stufe mehr oder weniger bis zur
        technischen und sinnvollen Grenze.
        :param  mehr  bool  True=mehr, False=weniger Helligkeit gewünscht
        """

    @abstractmethod
    def led_schalten(self, kanal, ein):
        """Schaltet die LED auf 'kanal' in den Zustand 'ein'.
        :param  kanal  int   Nummer des Anschlusses der LED in der Kette
        :param  ein    bool  Zustand ein (True) oder aus (False)
        """

    @abstractmethod
    def ist_led_ein(self, kanal):
        """Ermittelt ob die LED auf 'kanal' eingeschalten ist.
        :param  kanal  int  Nummer vom Anschluss der LED in der Kette
        :returns      bool  True wenn ein, False wenn aus
        """

    @abstractmethod
    def leds_nun_aendern(self):
        """Die vorgenommenen Änderungen an den Schaltzuständen der LEDs werden
        an die LED übermittelt und übernommen.
        """

    @abstractmethod
    def abschalten(self):
        """Abschalten aller LEDs.
        """

# -------------------------------------------------------------------------- #
class ABC_VGS80PultEingabeHW(ABC):
    """<i>Abstrakte</i> Basis-Klasse für Platinen, welche die Erkennung der
    Tasten des Pultes übernehmen. Die hier definierten, abstrakten Methoden müssen
    von einer Kind-Klasse spezifisch für die Platine implementiert werden.
    """
    # pylint: disable=too-few-public-methods
    # hier gibt es (bislang jedenfalls) keine Notwendigkeit für mehr Methoden

    @abstractmethod
    def __init__(self, max_kanal):
        """Initialisierung der Hardware.
        :param max_kanal  int  höchste benötigte Kanalnummer einer Taste (zero basiert)
        """
        melde(MTyp.DEBUG, 'Wurde abstraktes __init__ in EingabeHardware implementiert?')

    @abstractmethod
    def hole_tasten(self):
        """Prüft alle Inputs und gibt alle gedrückten Tasten ohne weitere
        Filterung oder Reihung zurück.
        :returns    liste von zumindest zwei Tastencodes
        """

# ------------------------------------------------------------- Ende Gelände #

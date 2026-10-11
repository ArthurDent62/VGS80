"""
Ansteuerung der Hardware Adafruit TLC5947 über den SPI Bus des Raspberry.
Damit die LEDs beim Start des Systems nicht alle gleichzeitig leuchten, ist
eine Relaisgruppe nach dem 24V Trafo gesetzt; die 24V Versorgung eines Rahmen
ist an den NO Ausgang eines Relais gelegt. Erst nach Initialisierung der TLC
Platinenkette wird das Relais geschalten und Strom für die LED verfügbar.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-06-15 wh Klasse begonnen von Demo-Script
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

try:
    import board
    import busio
    import digitalio

    import adafruit_tlc5947
except ImportError:
    raise ImportError('Problem mit einer Adafruit Bibliothek!')

from c_basis import ABC_VGS80PultAusgabeHW
from daten_basis import RAHMEN_ON
from m_ausgaben import MeldeTyp as MTyp, melde

# -------------------------------------------------- modulweite Definitionen #
# --- Konstante
_PINS_PER_PLAT = 24
_LATCH_PIN = board.D25              # pin 22 on Raspberry Pi 3B+
_PIN_RELAIS_RAHMEN1 = board.D27     # pin 13
_PIN_RELAIS_RAHMEN2 = board.D22     # pin 15
_LED_HELL_MAX = 0xEFF
_LED_HELL_MIN = 0x2FF
_LED_HELL_DELTA = 0x300

# ------------------------------------------------------------------- Klasse #
class AusgabeHardware(ABC_VGS80PultAusgabeHW):
    """Die Hardware für die Ausgabe von Befehlen an die LEDs über eine Kette
    von TLC5947 Boards. Muss alle abstrakten Methoden der Basisklasse befüllen.
    """

    def __init__(self, max_kanal):
        """Initialisierung der Boards.
        Implementierung.
        :param max_kanal  int  höchste benötigte Kanalnummer einer LED (zero basiert)
        """
        # pylint: disable=super-init-not-called
        # Ableitung von abstrakter Methode erkennt pylint nicht

        # Für benötigte Rahmen die Relais-Pins definieren
        if not (RAHMEN_ON[0] or RAHMEN_ON[1]):
            melde(MTyp.FEHLER, f'Kein Rahmen zum Einschalten von LED gegeben!')

        self.rahmen_relais = [digitalio.DigitalInOut(_PIN_RELAIS_RAHMEN1), \
                              digitalio.DigitalInOut(_PIN_RELAIS_RAHMEN2)]

        # Pins konfigurieren und Strom für LEDs definitiv abschalten
        for rr in self.rahmen_relais:
            rr.switch_to_output(True)
            rr.value = True         # Steuerkreis auf HI, damit Relais aus

        # berechne die notwendigen Platinen
        self.anz_platin = (1 + max_kanal) // _PINS_PER_PLAT

        # SPI bus initialisieren
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
        try:
            # entgegen der Beschreibung gibt's Fehler; ev. später?
            melde(MTyp.IMMER, f'Frequenz vom SPI Bus: {spi.frequency:,}')
        except AttributeError:
            melde(MTyp.IMMER, 'Frequenz vom SPI Bus in dieser Version nicht eruierbar.')

        # TLC5947 initialisieren
        latch = digitalio.DigitalInOut(_LATCH_PIN)
        self.led_kette = adafruit_tlc5947.TLC5947(spi, latch, \
                                num_drivers=self.anz_platin, auto_write=False)

        # alle LED erstmal abschalten
        for kanal in range(1 + max_kanal):
            self.led_kette[kanal] = 0
        self.leds_nun_aendern()

        # da die LED nun abgeschalten sind, kann das Relais aktiviert werden
        for rr, ron in zip(self.rahmen_relais, RAHMEN_ON):
            rr.value = not ron        # Steuerkreis auf LO, Relais ein

        # merke die eingeschalteten LEDs, für Änderung der Helligkeit nötig
        self.led_ein = [False] * (1 + max_kanal)

        # die initiale Helligkeit merken
        self.hellig = (_LED_HELL_MIN + _LED_HELL_MAX)//2

    # ---------------------------------------------------------------------- #
    def led_schalten(self, kanal, ein):
        """Schaltet die LED auf 'kanal' in den Zustand 'ein'.
        Implementierung.
        :param  kanal  int   Nummer des Anschlusses der LED in der Kette
        :param  ein    bool  Zustand ein (True) oder aus (False)
        """
        self.led_ein[kanal] = ein
        self.led_kette[kanal] = self.hellig if ein else 0

    # ---------------------------------------------------------------------- #
    def ist_led_ein(self, kanal):
        """Ermittelt ob die LED auf 'kanal' eingeschalten ist.
        Implementierung.
        :param  kanal  int  Nummer vom Anschluss der LED in der Kette
        :returns      bool  True wenn ein, False wenn aus
        """
        return self.led_ein[kanal]

    # ---------------------------------------------------------------------- #
    def helligkeit(self, mehr):
        """Verändert die Helligkeit um eine Stufe mehr oder weniger bis zur
        technischen und sinnvollen Grenze.
        Implementierung.
        :param  mehr  bool  True=mehr, False=weniger Helligkeit gewünscht
        """
        if mehr:
            self.hellig = min(_LED_HELL_MAX, self.hellig + _LED_HELL_DELTA)

        else:
            self.hellig = max(_LED_HELL_MIN, self.hellig - _LED_HELL_DELTA)

        melde(MTyp.DEBUG, f'LED-Helligkeit = {self.hellig:X}')

        # alle (eingeschalteten?) LED entsprechend ändern
        for kanal in range(self.anz_platin * _PINS_PER_PLAT):
            if self.led_ein[kanal]:
                self.led_kette[kanal] = self.hellig

    # ---------------------------------------------------------------------- #
    def leds_nun_aendern(self):
        """Schreibt vorgenommene Änderungen an den Soll-Zuständen der LEDs
        an die Treiber-Kette.
        Implementierung.
        """
        self.led_kette.write()

    # ---------------------------------------------------------------------- #
    def abschalten(self):
        """Abschalten aller LEDs.
        Implementierung.
        """
        for rr in self.rahmen_relais:
            rr.value = True     # Steuerkreis auf HI, Strom aus!
            rr.deinit()         # freigeben des Pin

# ------------------------------------------------------------- Ende Gelände #

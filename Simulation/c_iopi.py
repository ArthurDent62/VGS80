"""
Ansteuerung der Hardware IO-Pi mittels I2C bus.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-28 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

try:
    from IOPi import IOPi
except ImportError:
    raise ImportError('Problem mit der IOPi Bibliothek!')

from c_basis import ABC_VGS80PultEingabeHW
from daten_basis import Taste, IOPI_ADRESSEN
from m_ausgaben import MeldeTyp as MTyp, melde

# Konstante
_PINS_PER_PORT = 8                  # Anzahl der Pins pro Port
_PINS_PER_ADR = _PINS_PER_PORT *2   # Anzahl der Pins pro Adresse am Bus
_PINS_PER_PLAT = _PINS_PER_ADR *2   # Anzahl der Pins pro Platine

# Variable
_letzte_fehler_posi = -1    # Position = Kanal der letzten Fehlermeldung

# -------------------------------------------------------------------------- #
class EingabeHardware(ABC_VGS80PultEingabeHW):
    """Das Einlesen von Tasten über IO-Pi Boards.
    """

    def __init__(self, max_kanal):
        """Initialisierung der Boards.
        Implementierung.
        :param  int  max_kanal  höchste verwendete Kanalnummer einer Taste (zero basiert)
        """
        # pylint: disable=super-init-not-called
        # Ableitung von abstrakter Methode erkennt pylint nicht

        # prüfe ob ausreichend Kanäle vorhanden sind
        if len(IOPI_ADRESSEN)*_PINS_PER_ADR < max_kanal + 1:
            raise ValueError(f'c_iopi: nicht genügend Platinen für die Tasten definiert!')

        # initialisiere die Chips-Daten
        self._bus = []
        for adr in IOPI_ADRESSEN:
            self.neu_bus(adr)

        # initialisiere die Port-Gruppen (2 je Bus)
        for inbus in self._bus:
            print(f'konfiguriere bus {inbus.myname:0x}', end='', flush=True)
            for group in range(2):
                inbus.set_port_direction(group, 0xFF)     # alle Ports 1=Input
                inbus.set_port_pullups(group, 0xFF)       # interner Pullup für alle Ports
                inbus.invert_port(group, 0xFF)            # 1 = gedrückte Taste

                print(f'  - group {group}', end='', flush=True)
            print()

    # ---------------------------------------------------------------------- #
    def neu_bus(self, adresse):
        """neues Bus-Objekt hinzufügen
        """
        self._bus.append(IOPi(adresse))
        self._bus[-1].myname = adresse

    # ---------------------------------------------------------------------- #
    def hole_tasten(self):
        """Prüft alle Inputs und gibt alle gedrückten Tasten ohne weitere
        Filterung oder Reihung zurück.
        Implementierung.
        :returns    liste von zumindest zwei Tastencodes
        """
        gedrueckt = [Taste.NIX, Taste.NIX]

        for nrbus, inbus in enumerate(self._bus):
            #print(f'bus={nrbus}', end='', flush=True)
            for group in range(2):
                # schneller: gleich alle 8 Pins übertragen statt einzeln
                port_group = inbus.read_port(group)

                #print(f'({port_group})  ', end='', flush=True)
                #print(f' -gruppe={group} ({port_group})', end='', flush=True)
                if port_group:
                    # einer der Pins ist aktiv, nur welche(r)?
                    _welche_tasten(nrbus*_PINS_PER_ADR \
                                        + group*_PINS_PER_PORT, port_group, gedrueckt)
        #print()
        return gedrueckt

# -------------------------------------------------------------------------- #
def _welche_tasten(anfang, bits, res):
    """Prüft alle Bits eines Ports und VERÄNDERT die Liste der Tasten!
    :param  anfang:     erste Kanalnummer dieser Bits
    :param  bits:       Bits der Gruppe
    :param  res:        (aktualisierte) Liste der Tasten
    """
    global _letzte_fehler_posi

    # durchforsten der Bits
    for b in range(8):
        if bits & 1<<b:
            # wir haben also ein gesetztes Bit gefunden
            posi = anfang + b
            try:
                # finde die Taste mit der Kanalnummer; nur eine Taste
                # kann diese Kanalnummer haben (wenn geprüft wurde)
                tneu = [t for t in Taste if t.kanal == posi].pop()
            except IndexError:
                # Fehlermeldung nur einmal je Kanal ausgeben
                if _letzte_fehler_posi != posi:
                    _letzte_fehler_posi = posi
                    melde(MTyp.FEHLER, \
                          f'IndexError: Taste an Kanal {posi} nicht definiert!')
                return

            # nun die neue Taste einsetzen
            res.append(tneu)
            try:
                # und dafür eine NIX-Taste entfernen, wenn vorhanden
                res.remove(Taste.NIX)
            except ValueError:
                pass

# ------------------------------------------------------------- Ende Gelände #

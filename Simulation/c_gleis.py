"""
Repräsentation der Gleisabschnitte.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.5 2019-12-19 wh Datei mit Klasse Gleis begonnen
# -------------------------------------------------------------------------- #
from enum import Flag, auto
import inspect

from m_pult_ausgabe import schalte_led as sled
from m_ausgaben import MeldeTyp as MTyp, melde

# ----------------------------------------------------- Konstante definieren #
# pylint: disable=bad-whitespace
# Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht

IDX_FREI = 0        # Kanäle der weissen LEDs der zugehörigen Gleismelder
IDX_ROT  = 1        # Kanäle der roten LEDs der zugehörigen Gleismelder
IDX_FS   = 2        # Abschnitt gehört derzeit zu dieser Fs
IDX_ZUSTAND = 3     # GZustand des Abschnitts

# pylint: enable=bad-whitespace
# -------------------------------------------------------------------------- #
class GZustand(Flag):
    """Darstellung des aktuellen Zustands eines Abschnitts.
    """
    FINSTER = 0         # frei, keine Fahrstrasse
    FAHRSTR = auto()    # Teil einer Fahrstrasse
    BELEGT = auto()     # da steht grad ein Schienenfahrzeug drauf
    FSZSS = auto()      # ist Zugschlussstelle der Fahrstrasse

# -------------------------------------------------------------------------- #
class Gleis():
    """Die Repräsentation der Gleisabschnitte.
    """

    def __init__(self, g_dict):
        """Initialisierung der Gleisabschnitte und deren Daten.
        :param  g_dict    dict   Daten der Gleisabschnitte
        """
        # Daten übernehmen
        # Struktur: Gleisbezeichnung => Array mit Daten, mit IDX_* als Zeiger
        self.gleise = {}

        for k, v in g_dict.items():
            self.gleise[k] = [v[0], v[1], None, GZustand.FINSTER]
            self.setze_anzeige(k)

    # ---------------------------------------------------------------------- #
    def setze_anzeige(self, abschnitt):
        """Gestaltet die Anzeige aufgrund des inneren Zustands eines Abschnitts.
        Wenn belegt, dann rot. Sonst: wenn Fahrstraße dann weiss. Sonst: finster.
        :param  abschnitt   str   Bezeichnung des Gleisabschnitts
        """
        weiss, rot, _, zustand = self.gleise[abschnitt]

        # mal alles ausschalten
        for kanal in weiss:
            sled(kanal, False)
        for kanal in rot:
            sled(kanal, False)

        # Farben nach Zustand schalten
        if zustand & GZustand.BELEGT:
            for kanal in rot:
                sled(kanal, True)
        elif zustand & GZustand.FAHRSTR:
            for kanal in weiss:
                sled(kanal, True)

    # ---------------------------------------------------------------------- #
    def fahrstr_erzeugen(self, fs, abschnitte, fszss):
        """Erzeugt eine Fahrstrasse über die benannten Gleisabschnitte.
        :param  fs     obj  Fahrstrasse
        :param  abschnitte  str  Menge der Gleisabschnitte der Fahrstrasse
        :param  fszss  str  Fahrstrassen-Zugschlussstelle
        :return True wenn zumindest einer der Gleisabschnitte belegt ist
        """

        ist_belegt = False

        for abschnitt in abschnitte:
            daten = self.gleise[abschnitt]

            # gross Problem wenn ein Abschnitt bereits Teil einer Fs ist
            # weil das darf eigentlich gar nicht vorkommen!
            if daten[IDX_ZUSTAND] & GZustand.FAHRSTR:
                fun = inspect.currentframe().f_code.co_name
                melde(MTyp.FEHLER, f'** {fun}: {abschnitt} ' + \
                      'ist bereits Teil einer Fahrstrasse, aber dürfte nicht!')
                break       # Rest braucht nicht geprüft werden

            # zurückmelden wenn ein Abschnitt belegt ist
            ist_belegt |= bool(daten[IDX_ZUSTAND] & GZustand.BELEGT)

            daten[IDX_FS] = fs
            daten[IDX_ZUSTAND] |= GZustand.FAHRSTR
            if abschnitt == fszss:
                daten[IDX_ZUSTAND] |= GZustand.FSZSS

            # ausleuchten
            self.setze_anzeige(abschnitt)

        return ist_belegt

    # ---------------------------------------------------------------------- #
    def fahrstr_loeschen(self, abschnitte):
        """Löst eine Fahrstrasse über die Gleisabschnitte auf.
        :param  abschnitte  str   Menge der Gleisabschnitte der Fahrstrasse
        """
        # pylint: disable=invalid-unary-operand-type
        # er versteht das auto() in Flag nicht
        for abschnitt in abschnitte:
            daten = self.gleise[abschnitt]
            daten[IDX_FS] = None
            daten[IDX_ZUSTAND] &= ~GZustand.FAHRSTR
            daten[IDX_ZUSTAND] &= ~GZustand.FSZSS

            # ausleuchten
            self.setze_anzeige(abschnitt)

    # ---------------------------------------------------------------------- #
    def belegung(self, abschnitt, ist_belegt):
        """Änderung in der Belegung eines Gleisabschnittes; für den Aufruf durch
        die Gleisfreimeldeanlage oder Simulation in GUI. TODO_Phase4 TODO_Phase5
        :param  abschnitt   str   Gleisabschnitt
        :param  ist_belegt  bool  True=Gleisabschnitte ist nun belegt
        """
        # pylint: disable=invalid-unary-operand-type
        # er versteht das auto() in Flag nicht
        _, _, fs, zustand = self.gleise[abschnitt]
        if ist_belegt:
            if zustand & GZustand.BELEGT:
                return          # ist eh schon belegt gemeldet
            # else
            zustand |= GZustand.BELEGT      # Zustand notieren

        else:       # nicht belegt
            if zustand & GZustand.BELEGT:
                if zustand & GZustand.FSZSS:
                    fs.aufloesen()          # an FS melden zum auflösen
            else:
                return          # war eh schon frei

        # neu ausleuchten
        self.setze_anzeige(abschnitt)

    # ---------------------------------------------------------------------- #
    def show_status(self):
        """Zeigt den Status des Melders am Bildschirm an (debug).
        """
        melde(MTyp.DEBUG, \
              f'Gleisabschnitte: {self.gleise}')

# ------------------------------------------------------------- Ende Gelände #

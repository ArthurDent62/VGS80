"""
Repräsentation einer Fahrstrasse.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-04-06 wh Klasse begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

import m_basis          # einzeln importierte Variablen werden nicht aktualisiert!
from daten_basis import Taste
from c_basis import FahrZustand
from m_ausgaben import MeldeTyp as MTyp, melde
from m_common import TastenTyp

# -------------------------------------------------------------------------- #
class Fahrstrasse():
    """Repräsentation einer Fahrstrasse.
    """
    # pylint: disable=too-many-instance-attributes
    # das ist eben ein komplexes Objekt

    # ---------------------------------------------------------------------- #
    def __init__(self, von_nach, weichen, signale, eks, fsaus, gleise, fszss):
        """Initialisierung der Fahrstrasse und ihrer Daten.
        :param  von_nach  tuple Tasten der Signale (ST-von, ST-nach)
        :param  weichen   dict  Weichen und notwendige Stellung {WT:Stellung}
        :param  signale   set   (Verschub-)Signale die Verbot zeigen müssen
        :param  eks       set   Eisenbahnkreuzungen
        :param  fsaus     set   Fahrstrassenausschlüsse
        :param  gleise    set   Gleisabschnitte für die Fs
        :param  fszss     str   Name des Gleisabschnitts Fahrstrassenzugschlussstelle
        """
        # pylint: disable=too-many-arguments
        # diese Initialisierung braucht halt viele Werte

        # Übernahme und Auswertung der Parameter
        self._taste_von, self._taste_nach = (Taste[x] for x in von_nach)
        self._weichen = {Taste[k]:v for k, v in weichen.items()}
        self._signale = set(Taste[s] for s in signale)
        self._eks = eks
        self._fsaus = fsaus
        self._gleise = gleise
        self._fszss = fszss
        self._ist_einfahrt = self._taste_von.typ == TastenTyp.ES

        try:
            self._start = m_basis.elemente[self._taste_von]    # Objekt Fahrstrassenanfang
        except IndexError:
            melde(MTyp.FATAL, f'Fahrstrassenstart nicht gefunden: {self._taste_von}')
        try:
            self._ziel = m_basis.elemente[self._taste_nach]    # Objekt Fahrstrassenziel
        except IndexError:
            melde(MTyp.FATAL, f'Fahrstrassenziel nicht gefunden: {self._taste_nach}')

        # Zustand der Fahrstrasse initialisieren
        self.__zustand = FahrZustand.NICHT

    # ---------------------------------------------------------------------- #
    def __str__(self):
        """Angepasste Ausgabe eines Strings für das Objekt Fahrstrasse.
        :returns String
        """
        return f'Fs von {self._taste_von} > {self._taste_nach}'

    # ---------------------------------------------------------------------- #
    def ist_ein(self):
        """Ist diese Fahrstrasse aktuell gestellt? => True
        :returns bool
        """
        return self.__zustand != FahrZustand.NICHT

    # ---------------------------------------------------------------------- #
    def aufloesen(self):
        """Auflösen der Fahrstrasse. Dies erfolgt in der Regel zugbewirkt,
        oder mit der FHT (dann doku-pflichtig, das passiert anderswo).
        """
        # Ausleuchtung der Fs am Pult zurücknehmen
        m_basis.abschnitte.fahrstr_loeschen(self._gleise)

        # nun den Verschluss der Verschubsignale und Weichen wieder aufschliessen
        self._verschluss_zuruecknehmen()

        # Zustand
        self.__zustand = FahrZustand.NICHT
        self._start.zugstrasse_loeschen()

    # ---------------------------------------------------------------------- #
    def _verschluss_zuruecknehmen(self):
        """Auflösen der Verschlüsse einer Fahrstrasse.
        Alle angesprochenen Objekte müssen es aushalten, dass sie ggf.
        noch gar nicht verschlossen wurden.
        """
        # Verschubsignale
        for sig in self._signale:
            m_basis.elemente[sig].aufschluss(self)

        # Weichen
        for taste, _ in self._weichen.items():
            m_basis.elemente[taste].aufschluss(self)

        # Fahrstrassenziel
        self._ziel.kein_ziel(self)

    # ---------------------------------------------------------------------- #
    def stellen(self):
        """Stellen der Fahrstrasse nach §16. Sind nicht alle Voraussetzungen
        erfüllt, läuft die Fahrstrasse nicht ein oder nur als Zughilfsstrasse.
        :return    Flag FahrZustand, Status der gebildeten Fahrstrasse.
        """
        # pylint: disable=too-many-return-statements
        # Ich empfinde es dennoch als übersichtlicher mit early-exit-returns

        # ------- TASTENDRUCK WIRKSAM?
        melde(MTyp.INFO, f'geht {self}?')
        # kann diese Fs aufgewertet werden?
        if self.__zustand & FahrZustand.ZUG:
            return self.__zustand       # Stop - bereits als Zugstraße vorhanden!

        melde(MTyp.INFO, 'kein Selbstausschluss')
        # Fahrstrassenausschluss prüfen §16 (2) c)
        for fs in self._fsaus:
            if m_basis.fahrstrassen[fs].ist_ein():
                return self.__zustand   # Stop - kollidierende Fs ist gerade aktiv

        melde(MTyp.INFO, 'kein Fs-Ausschluss')
        # Fahrstrassenziel erlaubt? §16 (2) d)
        if not self._ziel.wird_ziel(self):
            return self.__zustand   # Stop - Ziel kann nicht angefahren werden

        melde(MTyp.INFO, 'Ziel erlaubt')
        # ------- VERSCHLIESSEN
        # Weichen prüfen & verschliessen nach §16 (2) a) & (2) 2.Abs -1
        for taste, links in self._weichen.items():
            if not m_basis.elemente[taste].verschluss(self, links):
                # also es hat nicht geklappt, dann wieder aufschliessen
                self._verschluss_zuruecknehmen()
                return self.__zustand

        melde(MTyp.INFO, 'Weichen verschlossen')
        # Verschubsignale prüfen und verschliessen nach §16 (2) b) & (2) 2.Abs -2
        for sig in self._signale:
            if not m_basis.elemente[sig].verschluss(self):
                # also es hat nicht geklappt, dann wieder aufschliessen
                self._verschluss_zuruecknehmen()
                return self.__zustand

        melde(MTyp.INFO, 'VerschubS. verschlossen')
        # Verhinderung feindlicher Fahrstrassen §16 (2) 2.Abs -3
        self.__zustand = FahrZustand.TEILS

        # Ausleuchtung am Pult §16 (2) 2.Abs -4
        belegt = m_basis.abschnitte.fahrstr_erzeugen(self, self._gleise, self._fszss)

        # ------- Weiter zu §16 (2) 3.Abs
        # TODO_Phase3 §16 (2) 3.Abs -3: EK?
        ek_offen = False
        if ek_offen:
            # es kommt keine fahrstrasse zustande, sie bleibt teilweise eingelaufen
            return self.__zustand

        # ------- ZUG HILFS STRASSE
        # es wurde eine Zughilfsstrasse erreicht
        self.__zustand = FahrZustand.HILFS

        # ------- FESTLEGEN?
        # §16 (2) 3.Abs -1: Weichen? ok wenn wir hierher kommen
        # §16 (2) 3.Abs -2: Verschubsignale nicht gestört? dzt. keine Prüfung
        # §16 (2) 3.Abs -4: Fahrweg frei gemeldet?
        if belegt:
            return self.__zustand

        melde(MTyp.INFO, 'alle Gleisabschnitte frei')
        # TODO_Phase3 §16 (2) 3.Abs -5: Streckenblock lässt die Fahrt zu?
        # pylint: disable=using-constant-test
        if False:
            return self.__zustand

        # ------- ZUGSTRASSE
        melde(MTyp.INFO, f'Zugstraße eingelaufen: {self} !')
        self.__zustand = FahrZustand.ZUG

        # ein AS bekommt bei einer Einfahrt jedesmal das zur Zugstrasse ...
        # ...gehörende ES als sein Vorsignal gesetzt
        if self._ist_einfahrt:
            self._ziel.vs_setzen(self._start)

        # §16 (2) 4.Abs -1: Fs-überwachungsmelder an
        # §16 (2) 4.Abs -2: Signal geht frei
        # erledigt Signal durch den Rückgabewert
        return self.__zustand

    # ---------------------------------------------------------------------- #
    def show_status(self):
        """Zeigt den Status des Signals am Bildschirm an (debug).
        """
        status = f'{self}:  '
        if self.__zustand & FahrZustand.ZUG:
            status += 'Zugstrasse '
        elif self.__zustand & FahrZustand.HILFS:
            status += 'ZugHilfsStr'
        elif self.__zustand & FahrZustand.TEILS:
            status += 'Fahrstrasse'
        else:
            status += 'keine Str. '

        melde(MTyp.DEBUG, status)

# ------------------------------------------------------------- Ende Gelände #

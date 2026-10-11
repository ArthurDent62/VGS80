"""
Prüft die Daten.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-01 wh Modul begonnen
# 0.1 2019-04-30 wh Umstellung xls nur Igel & Platz, Kanal wird berechnet
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #
# pylint: disable=too-many-lines
# wenn jemand weiss wie das Modul übersichtlicher wird, gern

from sys import stderr
from datetime import datetime
from pathlib import Path
from enum import Enum, unique

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.formatting.rule import CellIsRule

from m_common import TastenTyp
from m_datei import k_start, k_zeile, k_ende
from m_tools import wsSet, col_ltr, col_nmbr, xls_range

# Konstante (für Excel-Ausgabe)
_DATEI_BELEG_EXT = r'_Beleg.xlsx'
_BLATT_IGEL = r'Anschlüsse'
_DATEI_AUFBAU = 'mehr'
_DATEI_GRUND = 'basis'
_BESCH_AUFBAU = 'Definition jener Daten welche die Basis-Daten verwenden.'
_BESCH_GRUND = 'Definition der grundlegenden Daten, auf denen andere Daten aufbauen.'

_PIN_FREI = '---'
_PIN_GND = 'GND'
_SPANNUNG_LED = '+24V'

# dict{Signaltyp : ( Klassendatei, Klassenname, such_Vorsignal, suchVGrM)}
_SIGNAL_KLASSEN = \
       {'VerS' : ('c_signal_versch', 'VerschubSignal', False, False), \
        'EVS' : ('c_signal_evs', 'EinfahrVorsignal', False, False), \
        'ES+AVS' : ('c_signal_es', 'EinfahrSignal', True, False), \
        'AS+VerS' : ('c_signal_as', 'Ausfahr_VerschubSignal', False, True), \
        'Ausfahrt' : ('c_signal_strecke', 'Strecke', False, False)}

# dict{MelderKürzel : (Klassenname, <kommt_noch_was?>)}
_MELDER_KLASSEN = \
        {'VGrM_H' : ('VGrM', ), \
         'VGrM_R' : ('VGrM', )}

_STYLE_INDEX = 'Index'
_STYLE_UEBER = 'Ueberschrift'
_TXT_ERR = 'X-X-X'
_TXT_IGEL = 'Igel'

_KANAL2DIFF = 12     # Abstand der Kanalnummern bei Doppel-LEDs

# Datenstrukturen
bf = set()          # die Kürzel der Bahnhöfe am Pult
fs = {}             # Fahrstrasse : (von_nach, w, s, e, f, g, fszss)
gleis = {}          # Gleisabschnitt : ({led_weiss}, {led_rot})
igels = {}          # { name : { port : (bezeich, (kanal_A1,kanal_B2,C3)) }}
_IGELS_TYP_IDX = -1 # missbrauchter Port-Index für den Igeltyp
_IGELS_SEQ_IDX = -2 # missbrauchter Port-Index für die Ausgabe-Reihenfolge
_IGELS_ID_IDX = -3  # missbrauchter Port-Index für die ID vom IOPi+
lange_as = {}       # Verweis Taste langes AS { t_name_lang : t_name_kurz }
leds = {}           # Funktionsbeschreibung logischer LED-Kanäle { k : Beschreib }
melder = {}         # Melder ganzes Pult { name : (li_kanal, re_kanal/None, beschr) }
rahmen = (False,) * 2   # Welche Rahmen werden verwendet?
spezi_melder = {}   # Melder/Bf {name: (basisname, liLed, reLed/None, beschr)}
signale = {}        # {t_signal.name : (TastenTyp, Bf, SignalBezeich, (*LEDs))}
tasten = {}         # {logischer_Kanal : (Name, TastenTyp, Beschreibung)}
vorsignale = {}     # dict[bahnhof][vorsignal_name] = VorsignalTaste
weichen = {}

# ------------------------------------------------------------------ Klassen #
@unique
class IgelTyp(Enum):
    """Zur Unterscheidung der verschiedenen Typen der Steckigel.
    """
    # pylint: disable=bad-whitespace
    # Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht
    LED_1  = ('LED', 1, 24, 0, 2,  1)
    LED_2  = ('LED', 2, 24, 0, 2, 13)
    TASTEN = ('TAS', 1, 16, 1, 1,  1)

    # eigener Konstruktor
    def __init__(self, typ, anz_leiter, pinouts, pinstart, steckzeilen, \
                 steckspalt1):
        """Initialisierung der Enum.
        :param typ         str  Igel-Typ (LED oder Taste)
        :param anz_leiter  int  Anzahl Leitungen die gesteuert werden (I/O)
        :param pinouts     int  Anzahl Pins eines Chips der Platine
        :param pinstart    int  auf der Platine, niedrigste Nummer des Pin
        :param steckzeilen int  Anzahl der Steckerzeilen
        :param steckspalt1 int  Nummer der 1. Steckerspalte
        """
        # pylint: disable=too-many-arguments
        # Workaround wäre ein Tupel draus zu machen, auch nicht besser lesbar
        if anz_leiter < 1 or pinouts < 1 or steckzeilen<1:
            raise ValueError('IgelTyp.__init__ says: nur positive Werte für ' + \
                             f'anz_leiter={anz_leiter} ** ' + \
                             f'pinouts={pinouts} ** steckzeilen={steckzeilen}!')

        # initialize
        self.typ = typ
        self.anz_leiter = anz_leiter
        self.pinouts = pinouts
        self.pinstart = pinstart
        self.steckzeilen = steckzeilen
        self.steckspalt1 = steckspalt1

        self.__class__.max_spalten = max(pinouts // steckzeilen,
                                         self.__class__.__dict__.get('max_spalten',0))

    # ------------------------------------------------------------- #
    @classmethod
    def find(cls, typ, anz_leiter):
        """Retourniert den Igeltyp welcher zu den gegebenen Parametern passt.
        :param  typ        der eigentliche Typ vom Igel
        :param  anz_leiter Anzahl der gesteuerten Leiter
        """
        for it in cls.__members__.values():
            if it.typ != typ:
                continue
            if it.anz_leiter == anz_leiter:
                return it
        raise ValueError(f'no such Igeltyp: typ={typ} mit {anz_leiter} Leiter!')

    # ------------------------------------------------------------- #
    @classmethod
    def anzahl_spalten(cls):
        """Gibt die maximale Anzahl an Spalten für die Ausgabe zurück.
        """
        return cls.max_spalten

    # ------------------------------------------------------------- #
    def anz_kanal(self):
        """Retourniert die Anzahl der Kanäle für einen Anschluss an diesem
        IgelTyp."""
        return 1 if self.anz_leiter==1 else 2

    # ------------------------------------------------------------- #
    def max_anz_stecker(self):
        """Retourniert die Anzahl der Stecker, welche für die Anzahl der
        Pins des jeweiligen IgelTyp benötigt werden.
        """
        return self.pinouts // self.anz_kanal()

# ----------------------------------------------------------------- Methoden #
def neu_led_kanal(beschreib, kanal):
    """Fügt Daten einer LED in die Datenstruktur ein.
    :param beschreib textliche Beschreibung
    :param kanal    Nr. auf der gesamten Kette der LED-Boards
    :return         True bei einem Fehler; sonst False
    """
    try:
        old = leds[kanal]
        # wenn erfolgreich, dann kanal schon belegt -> Fehler
        print(f'\n  *** LED-Kontakt {kanal} schon belegt ! ***')
        print('  ' + beschreib)
        print('  ' + old)
        leds[kanal] = old + ' -XXXXX- ' + beschreib
        return True

    except KeyError:
        # nicht vorhanden -> neuer Kontakt -> aufnehmen
        leds[kanal] = beschreib
        return False

# -------------------------------------------------------------------------- #
def die_rahmen(r1, r2):
    """Definition, welche Rahmen eingeschalten werden müssen.
    :param r1, r2   True wenn der Rahmen verwendet wird, sonst False
    :return True    bei einem Fehler; sonst False
    """
    # Merken
    global rahmen
    rahmen = (r1, r2)

    # ein Rahmen muss mindestens angegeben sein!
    ok = (r1 or r2)

    if ok:
        print('\nRahmendefinition ist ok.', end='')
    else:
        print('\n  *** Ohne Rahmen kann das Pult nicht arbeiten!', end='')
    print(f' (R1: {r1} - R2: {r2})')

    return not ok

# -------------------------------------------------------------------------- #
def neu_igel(igel_name, abfolge, igel_typ):
    """Fügt die Basisdaten eines Igels in die Datenstruktur ein.
    :param igel_name  Name des Igels für den LED-Stecker
    :param abfolge    Position in der Reihenfolge der Steckigel
    :param igel_typ   IgelTyp für diesen Steckigel
    :return True      bei einem Fehler; sonst False
    """
    # Eindeutigen Namen prüfen
    try:
        _ = igels[igel_name]
        # wenn kein Fehler ist der Name schon vorhanden, das ist ein Fehler!
        print(f'\n  ** Igel {igel_name} bereits vorhanden!')
        return True

    except KeyError:
        # igel noch nicht vorhanden -> igel erzeugen
        igels[igel_name] = {_IGELS_TYP_IDX : igel_typ, \
                            _IGELS_SEQ_IDX : abfolge, \
                            _IGELS_ID_IDX  : None}

    return False

# -------------------------------------------------------------------------- #
def neu_tast_igel(igel_name, abfolge, igel_typ, igel_id):
    """Fügt die Basisdaten eines Igels in die Datenstruktur ein.
    :param igel_name  Name des Igels für den LED-Stecker
    :param abfolge    Position in der Reihenfolge der Steckigel
    :param igel_typ   IgelTyp für diesen Steckigel
    :param igel_id    soldered ID of IOPi plus Hardware
    :return True      bei einem Fehler; sonst False
    """
    # hinzufügen des Igels
    if neu_igel(igel_name, abfolge, igel_typ):
        # das hat nicht geklappt
        return True

    # neue ID zum Igel hinzufügen
    igels[igel_name][_IGELS_ID_IDX] = igel_id

    # die ID darf nun genau einmal vorhanden sein
    cntr = 0
    for exists in (value[_IGELS_ID_IDX] for value in igels.values() \
                   if value[_IGELS_ID_IDX] is not None):
        if exists == igel_id:
            cntr += 1

    if cntr != 1:
        print(f'\n  ** Fehler: IOPi+ ID: 0x{igel_id:x} mehrfach angegeben **')
        return True

    return False

# -------------------------------------------------------------------------- #
def _igel_sort(sk):
    """Funktion welche die Igel nach Typ (LED, Taste) und innerhalb nach
    ihrer Position am Bus oder in der Kette sortiert.
    """
    return (sk[1][_IGELS_TYP_IDX].typ, sk[1][_IGELS_SEQ_IDX])

# -------------------------------------------------------------------------- #
def neu_igel_platz(beschreib, igel_name, platz, pins):
    """Fügt Belegungsdaten eines Steckplatzes am Igel in die Datenstruktur ein.
    :param beschreib  textliche Beschreibung
    :param igel_name  Name des Igels für den LED-Stecker
    :param platz   Nummer des Steckplatzes am Igel
    :param pins    die Belegung der Steckerpins als tupel (A1, 2, 3)
    :return        True bei einem Fehler; sonst False
    """
    # 1. den Igel finden
    try:
        thisIgel = igels[igel_name]
    except KeyError:
        # igel noch nicht vorhanden -> dann fehlt er in der Liste im Excel!
        print(f'\n  ** Igel {igel_name} fehlt in der Liste der definierten Igel!')
        return True

    # 2. den Platz prüfen
    if platz < 0:
        print(f'\n  ** Igel {igel_name}: Platz {platz} darf nicht negativ sein! **')
        return True

    if platz >= thisIgel[_IGELS_TYP_IDX].max_anz_stecker():
        print(f'\n  ** Igel {igel_name}: hat keinen Platz {platz}! **')
        return True

# TODO 3. Igeltyp gewünscht gegen vorhanden prüfen    nötig?
#     if thisIgel[_IGELS_TYP_IDX] != igel_typ:
#         print(f'\n  ** Igel {igel_name} hat Typ {thisIgel[_IGELS_TYP_IDX]} :')
#         print(f'   Platz {platz} verlangt Typ {igel_typ} ! **')
#         return True

    # 4. den Stecker am Igel platzieren
    try:
        old = thisIgel[platz][0]
        # wenn erfolgreich, dann ist platz schon belegt -> Fehler
        print(f'\n  ** Stecker {igel_name}-{platz} schon belegt! **')
        print('  ' + beschreib)
        print('  ' + old)
        thisIgel[platz] = (old + ' -XXXXX- ' + beschreib, (_TXT_ERR, )*3)
        return True

    except KeyError:
        # nicht vorhanden -> neuer Kontakt -> aufnehmen
        thisIgel[platz] = (beschreib, pins)
        return False

# -------------------------------------------------------------------------- #
def rechne_kanal(igel_name, platz):
    """Berechnet die Kanalnummer für den Platz am Steckigel.
    :param igel_name    Name des Steckigels
    :param platz        Nummer des Steckplatzes
    :returns kanal      Nummer des Kanals an der Hardware
    """
    try:
        igel_typ = igels[igel_name][_IGELS_TYP_IDX]
        k = igel_typ.pinouts * igels[igel_name][_IGELS_SEQ_IDX] + platz
        return (k, k + _KANAL2DIFF)
    except KeyError:
        print(f'\n  ** Igel nicht in der Werteliste: {igel_name}')
        return (998, 999)

# -------------------------------------------------------------------------- #
def neu_2leds(beschreib, bPos, bNeg, igel_name, platz, kPos, kNeg):
    """Prüft die Daten einer LED und fügt sie in die Datenstrukturen ein.
    :param beschreib: textliche Beschreibung der LED
    :param bPos Beschreibung der positiven LED
    :param bNeg Beschreibung der negativen LED
    :param igel_name:    Name des Igels für den LED-Stecker
    :param platz:   Nummer des Steckplatzes am Igel
    :param kPos:    Nr. der positiven LED auf der Kette der Treiber-Boards
    :param kNeg:    Nr. der negativen LED auf der Kette der Treiber-Boards
    :return         True bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-arguments
    # manchmal brauchts eben viele Argumente... :)

    # print(f'{beschreib:28}  LED_Kanal={kanal:3},  Igel={igel_name:>3}.{platz}')

    # Datenprüfung
    fehler = False
    if bPos is None:
        print(f'\n  bPos ist None von ' + beschreib)
        fehler = True
    if bNeg is None:
        print(f'\n  bNeg ist None von ' + beschreib)
        fehler = True
    if platz is None:
        print(f'\n  platz ist None von ' + beschreib)
        fehler = True
    if kPos is None:
        print(f'\n  kPos ist None von ' + beschreib)
        fehler = True
    if kNeg is None:
        print(f'\n  kNeg ist None von ' + beschreib)
        fehler = True

    if igel_name is None:
        print(f'\n  igel_name ist None von ' + beschreib)
        fehler = True
    elif igels[igel_name][_IGELS_TYP_IDX].anz_leiter != 2:
        print(f'\n  {igel_name} ist nicht für 2 LED vorgesehen! ' + beschreib)
        fehler = True

    if fehler:
        return True     # bei Inkonsistenz war's das!

    # Daten scheinen in sich konsistent - übernehmen
    fehler  = neu_led_kanal(beschreib + bPos, kPos) # pylint: disable=bad-whitespace
    fehler |= neu_led_kanal(beschreib + bNeg, kNeg)

    return fehler | neu_igel_platz(beschreib+bPos+'*'+bNeg, igel_name, \
                             platz, (kPos, kNeg, _SPANNUNG_LED))

# -------------------------------------------------------------------------- #
def neu_1led(beschreib, igel_name, platz, kanal):
    """Prüft die Daten einer LED und fügt sie in die Datenstrukturen ein.
    :param beschreib: textliche Beschreibung der LED
    :param igel_name:    Name des Igels für den LED-Stecker
    :param platz:   Nummer des Steckplatzes am Igel
    :param kanal:   Nr. der LED auf der Kette der Treiber-Boards
    :return         True bei einem Fehler; sonst False
    """
    # print(f'{beschreib:28}  LED_Kanal={kanal:3},  Igel={igel_name:>3}.{platz}')

    # Datenprüfung
    fehler = False
    if platz is None:
        print(f'  platz ist None von ' + beschreib)
        fehler = True
    if kanal is None:
        print(f'  kanal ist None von ' + beschreib)
        fehler = True

    if igel_name is None:
        print(f'  igel_name ist None von ' + beschreib)
        fehler = True
    elif igels[igel_name][_IGELS_TYP_IDX].anz_leiter != 1:
        print(f'\n  {igel_name} ist nicht für 1 LED vorgesehen! ' + beschreib)
        fehler = True

    if fehler:
        return True     # bei Inkonsistenz war's das!

    # Daten scheinen in sich konsistent - übernehmen
    fehler = neu_led_kanal(beschreib, kanal)
    return fehler | neu_igel_platz(beschreib, igel_name, platz, \
                             (kanal, _PIN_FREI, _SPANNUNG_LED))

# -------------------------------------------------------------------------- #
def neu_taste(beschreib, igel_name, platz, typ, lang_text=''):
    """Prüft die Daten einer Taste und fügt sie in die Datenstrukturen ein.
    :param beschreib:  textliche Beschreibung der Taste
    :param igel_name:  Name des Igels für den LED-Stecker
    :param platz:      Nummer des Steckplatzes am Igel
    :param typ:        Typisierung der Taste laut TastenTyp
    :param lang_text:  lange Beschreibung der Taste, optional
    :return       True bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-arguments
    # manchmal braucht es eben viel Input

    # print(f'{beschreib:28}  TastenKanal={kanal:3},  Igel={igel_name:>3}.{platz},  ' \
            # + f'Typ={typ},  Lang={lang_text}')
    if igel_name is None:
        print(f'  igel_name ist None von ' + beschreib)
        return True
    if platz is None:
        print(f'  platz ist None von ' + beschreib)
        return True
    if typ.__class__ is not TastenTyp:
        print(f'  Typisierung ist kein TastenTyp: ' + beschreib)
        return True

    fehler = False
    kanal, _ = rechne_kanal(igel_name, platz)

    try:
        old = tasten[kanal]
        # wenn erfolgreich, dann kanal schon belegt -> Fehler
        print(f'\n  *** Tasten-Kontakt {kanal} schon belegt ! ***')
        print('  ' + beschreib)
        print('  ' + old[0])
        tasten[kanal] = (old[0] + ' -XXXXX- ' + beschreib, TastenTyp.NIX, "")
        fehler = True

    except KeyError:
        # nicht vorhanden -> neuer Kontakt -> aufnehmen
        tasten[kanal] = (beschreib, typ, lang_text)

    return fehler | neu_igel_platz(beschreib, igel_name, platz, \
                             (kanal, _PIN_GND, _PIN_FREI))

# -------------------------------------------------------------------------- #
def neu_melder(name, beschreib, li_kanal, re_kanal=None):
    """Fügt die Daten des Melders in die Datenstruktur ein.
    :param  name:       Kurzbezeichnung
    :param  beschreib:  textliche Beschreibung
    :param  li_kanal:   Nummer des Kanals der linken (oder einzigen) LED
    :param  re_kanal:   Nummer des Kanals der rechten LED (oder None)
    """
    melder[name.replace(' ', '_')] = (li_kanal, re_kanal, beschreib)

# -------------------------------------------------------------------------- #
def _neu_bahnhof(bhf):
    global bf
    bf.add(bhf)

# -------------------------------------------------------------------------- #
def bahnhofset():
    """Gibt die Menge aller Betriebsstellenkürzel zurück.
    """
    global bf
    return bf

# -------------------------------------------------------------------------- #
def neu_spezi_melder(name, beschreib, li_kanal, re_kanal=None, bhf=None):
    """Fügt die Daten des Melders in die Datenstruktur ein.
    :param  name:       Kurzbezeichnung
    :param  beschreib:  textliche Beschreibung
    :param  li_kanal:   Nummer des Kanals der linken (oder einzigen) LED
    :param  re_kanal:   Nummer des Kanals der rechten LED (oder None)
    :param  bhf         Betriebsstellenkürzel; Standard = für alle Bhf am Pult
    """
    fehler = False

    # unter welchem Namen eintragen?
    basisname = name.replace(' ', '_')
    elem_name = basisname
    if bhf is not None:
        _neu_bahnhof(bhf)
        elem_name = _mach_name(bhf, basisname)
        beschreib += f' in Bf. {bhf}'

    # ist die Taste schon vorhanden?
    try:
        alt = spezi_melder[elem_name]
        print(f'** Fehler: Melder {elem_name} ist mehrfach definiert:\n' \
              + f'alt: {alt} ** neu: ({li_kanal}, {re_kanal}, {beschreib})')
        fehler = True

    except KeyError:
        # alles gut, neuer Melder
        spezi_melder[elem_name] = (basisname, li_kanal, re_kanal, beschreib)

    return fehler

# -------------------------------------------------------------------------- #
def neu_fahrstrasse(fs_id, von_nach, w, s, e, f, g, fszss):
    """Fügt die Parameter einer Fahrstrasse zu den geprüften Daten.
    :param  fs_id      id     Bezeichnung der Fahrstrasse
    :param  von_nach   tuple  (Name Signal von, Name Signal nach)
    :param  w,s,e,f,g  set    Weichen, Signale, Ek, Fs-Ausschlüsse, Gleise der Fs
    :param  fszss      str    Fs-Zugschlussstelle der Fs
    :return  True   bei einem Fehler; sonst False
    """
    # pylint: disable=too-many-arguments
    # trotz vieler Argumente ist es übersichtlicher dargestellt was nötig ist
    try:
        _ = fs[fs_id]
        # wenn erfolgreich, dann ist Fahrstrasse schon definiert -> Fehler
        print(f'\n  ** Fahrstrasse {fs_id} schon definiert !  **')
        return True

    except KeyError:
        # nicht vorhanden -> ist neu -> aufnehmen
        fs[fs_id] = (von_nach, w, s, e, f, g, fszss)

    return False

# -------------------------------------------------------------------------- #
def neu_gleis(gid, kPos, kNeg):
    """Fügt die Parameter eines Gleisabschnitts zu den geprüften Daten.
    :param  gid     str    Gleisbezeichnung
    :param  kPos    set    Kanäle der positiven, weissen LEDs vom Gleis
    :param  kNeg    set    same, negativ, rot
    :return  True   bei einem Fehler; sonst False
    """
    try:
        _ = gleis[gid]
        # wenn erfolgreich, dann ist Gleisabschnitt schon definiert -> Fehler
        print(f'\n  ** Gleisabschnitt {gid} schon definiert !  **')
        return True

    except KeyError:
        # nicht vorhanden -> neuer Abschnitt -> aufnehmen
        gleis[gid] = (kPos, kNeg)

    return False

# -------------------------------------------------------------------------- #
def neu_weiche(taste, typ, bhf, init_links, led_list):
    """Fügt die Parameter einer Weiche zu den geprüften Daten.
    ACHTUNG: bei ortsbedienten Weichen ist ledKanLiBel None!
    :param  taste   str    Weichentaste
    :param  typ     char   'f'=fernbedient; 'o'=ortsbedient
    :param  bhf     str    Betriebsstellenkürzel
    :param  init_links bool  True wenn die Weiche nach links stehend starten soll
    :param  led_list  (int)  Kanäle der LEDs
    :return  True   bei einem Fehler; sonst False
    """
    try:
        _ = weichen[taste]
        # wenn erfolgreich, dann ist Weichentaste schon belegt -> Fehler
        print(f'\n  ** Weichen-Taste {taste} schon belegt !  **')
        return True

    except KeyError:
        # nicht vorhanden -> neue Weiche -> aufnehmen
        weichen[taste] = (typ, init_links, led_list)

    _neu_bahnhof(bhf)
    return False

# -------------------------------------------------------------------------- #
def neu_signal(taste, typ, bhf, sig_name, led_list):
    """Fügt die Parameter eines Signals zu den geprüften Daten.
    :param  taste   str    Name Signaltaste
    :param  typ     str    Signaltyp
    :param  bhf     str    Betriebsstellenkürzel
    :param  sig_name  str  Name des (Haupt)Signals
    :param  led_list (int)   Kanäle der LEDs
    :return         True   bei einem Fehler; sonst False
    """
    try:
        alt = signale[taste]
        # wenn erfolgreich, dann ist Signaltaste schon belegt -> Fehler
        print(f'\n  ** Signal-Taste {taste} schon belegt !  **')
        print(f'alt: {alt} * neu: {bhf} {sig_name}')
        return True

    except KeyError:
        # nicht vorhanden -> neues Signal -> aufnehmen
        signale[taste] = (typ, bhf, sig_name, led_list)

    _neu_bahnhof(bhf)
    return False

# -------------------------------------------------------------------------- #
def neu_vorsignal(bhf, vs_name, vs_taste):
    """Fügt eine Vorsignal in den Datenstamm hinzu.
    :param  bhf       str  Betriebsstellenkürzel
    :param  vs_name   str  Name des Vorsignals
    :param  vs_taste  str  Name Signaltaste
    """
    # hole die Liste der Vorsignale von Bahnhof bhf
    try:
        bhf_vs = vorsignale[bhf]
    except KeyError:
        bhf_vs = {}
        vorsignale[bhf] = bhf_vs

    _neu_bahnhof(bhf)
    bhf_vs[vs_name] = vs_taste

# -------------------------------------------------------------------------- #
def neu_as_lang(taste_lang, taste_kurz):
    """Fügt eine lange Einfahrt der kurzen hinzu.
    :param  taste_lang   str    Name Signaltaste lang
    :param  taste_kurz   str    Name Signaltaste kurz
    :return              True   bei einem Fehler; sonst False
    """
    try:
        _ = signale[taste_kurz]
    except KeyError:
        # nicht vorhanden -> kein Verweis auf Signal möglich!
        print(f'\n  ** Kein Signal für {taste_kurz} vorhanden !  **')
        return True

    try:
        _ = lange_as[taste_lang]
        # wenn erfolgreich, dann ist Signaltaste schon belegt -> Fehler
        print(f'\n  ** Signal-Taste {taste_lang} schon belegt !  **')
        return True
    except KeyError:
        # nicht vorhanden -> neues Signal -> aufnehmen
        lange_as[taste_lang] = taste_kurz
    return False

# -------------------------------------------------------------------------- #
def fs_konsistenz():
    """Konsistenzprüfung nach dem Einlesen aller Daten.
    :return  True  bei einem Fehler; sonst False
    """
    fehler = False

    # Fahrstrassenstart
    # die ES und AS
    t_signale = set(s for s in signale if signale[s][0] in ('ES+AVS', 'AS+VerS'))
    # Differenz zu den vorhandenen Fs-Starts
    fehlende = t_signale ^ set(v[0] for v in fs)
    if fehlende:
        print('\n  ** Fehler im Sperrenplan: diese Hauptsignale sind nicht ' + \
              f'Anfang einer Fahrstrasse: {fehlende} !')
        fehler = True

    # Fahrstraßenziele
    # die AS und Ausfahrt-Streckentasten sind Ziele
    t_signale = set(s for s in signale if signale[s][0] in ('Ausfahrt', 'AS+VerS'))
    # dazu kommen noch die langen Einfahrten am AS
    t_signale |= set(s for s in lange_as if signale[lange_as[s]][0] in ('Ausfahrt', 'AS+VerS'))
    fehlende = t_signale ^ set(v[1] for v in fs)
    if fehlende:
        print('\n  ** Fehler im Sperrenplan: diese Tasten sind nicht Ziele ' + \
              f'einer Fahrstrasse: {fehlende} !')
        fehler = True

    return fehler

# -------------------------------------------------------------------------- #
def _mach_name(bhf, name):
    """Erzeugt einen Namen aus Bahnhof und Elementnamen.
    :param  bhf    Bahnhof. Kürzel
    :param  name   Name des Elements
    """
    _neu_bahnhof(bhf)
    return f'{bhf}_{name}'

# -------------------------------------------------------------------------- #
def listen_schirm():
    """Listet die Anschlüsse in Reihenfolge am Bildschirm auf (ohne Lücken).
    """
    # LED
    input('Weiter mit Enter')
    print('\n ---- Liste LED ----')
    for k, v in sorted(leds.items()):
        print(f'{k:4} -> {v}')

    # Tasten
    input('Weiter mit Enter')
    print('\n ---- Liste Tasten ----')
    for k, v in sorted(tasten.items()):
        print(f'{k:4} -> {v[0]}')

    # Melder
    input('Weiter mit Enter')
    print('\n ---- Liste Melder ----')
    for k, v in sorted(melder.items()):
        print(f'{k:8} -> {v[2]}')

    # Igel
    input('Weiter mit Enter')
    print('\n ---- Liste Igel ----')
    for ki, vi in sorted(igels.items()):
        print('Igel: ' + ki)
        for k, v in sorted(vi.items()):
            if k < 0:       # die negativen Indices sind speziell
                continue
            print(f'{k:4} -> {v[0]}')

# -------------------------------------------------------------------------- #
def _belegt_blatt(wb):
    """Listet die Belegungen in Reihenfolge in ein Excel-Blatt.
    :param wb    Excel Workbook
    """
    # pylint: disable=too-many-locals,too-many-statements
    # es braucht unterschiedliche Fonts und Stile und Daten
    # ...und besser alles an einem Platz

    # lokale Konstante
    # pylint: disable=bad-whitespace, no-member
    # ...für visuelle Formatierung, pylint liegt falsch
    COL_LED_STAT = col_nmbr('A')
    COL_LED_GRP  = col_nmbr('B')
    COL_LED      = col_nmbr('C')
    COL_INDEX    = col_nmbr('D')
    COL_TASTE    = col_nmbr('E')
    COL_TYP      = col_nmbr('F')
    COL_TASTE_GRP= col_nmbr('G')
    COL_IGEL     = col_nmbr('I')
    ROW_START    = 2
    ROW_RAHMEN   = ROW_START + IgelTyp.LED_2.pinouts + 2    # Rahmen verwendet
    ROW_STATUS   = ROW_RAHMEN + 5       # LED-Status-String

    CLR_GROUP = 'AEBD07'
    CLR_IGEL = '0BEDEE'
    CLR_INDEX = 'D0A8D0'
    CLR_INPUT = 'FFFF00'    # voll gelb
    CLR_PORT = 'DAEABF'
#     CLR_WICHTIG = 'FFB533'
    CLR_AUS = '404040'
    CLR_GRUEN = '00B050'
    CLR_ORANGE = 'FFC000'
    CLR_ROT = 'FF0000'
    CLR_WEISS = 'FFFFFF'

    BREITE_GRP = 3
    BREITE_IGEL = 36
    BREITE_INDEX = 5
    BREITE_LED = 28     # default: 8,43 irgendwas
    BREITE_STATUS = 6
    BREITE_TASTE = 18
    BREITE_TYP = 9

    TXT_LED = 'LED-Kanal'
    TXT_LED_STRING = 'LED-Status-String:'
    TXT_LEER = ' . . . . . . . .'
    TXT_RAHMEN_INFO = 'Info zur Verwendung der Rahmen'
    TXT_RAHMEN_BEZ = 'Rahmen'
    TXT_STATUS = 'Status'
    TXT_TASTE = 'Taste-Kanal'
    TXT_TYP = 'Typ'
    # pylint: enable=bad-whitespace

    date_now = datetime.now()
    date_sec = ((date_now.day*24 + date_now.hour)*60 + date_now.minute)*60 + date_now.second
    # print(f'  **** ergeb: {date_sec} oder {date_sec:x}')
    blatt = f'Beleg{date_now.strftime("%Y%m%d.%H%M")}'

    ws = wb.create_sheet(blatt, 0)
    ws.freeze_panes = f'{col_ltr(COL_TASTE_GRP+1)}{ROW_START}'

    ws.sheet_properties.tabColor = f'{date_sec:06x}'

    # Überschriften .........
    hd_style = NamedStyle(_STYLE_UEBER)
    hd_style.font = Font(size=12, bold=True, italic=True)
    hd_style.alignment = Alignment(horizontal='center')
    wsSet(ws, 1, COL_LED_STAT, TXT_STATUS, hd_style)
    wsSet(ws, 1, COL_LED, TXT_LED, hd_style)
    wsSet(ws, 1, COL_TASTE, TXT_TASTE, hd_style)
    wsSet(ws, 1, COL_TYP, TXT_TYP, hd_style)

    # Spalten formatieren
    ws.column_dimensions[col_ltr(COL_LED_STAT)].width = BREITE_STATUS
    ws.column_dimensions[col_ltr(COL_LED_GRP)].width = BREITE_GRP
    ws.column_dimensions[col_ltr(COL_LED)].width = BREITE_LED
    ws.column_dimensions[col_ltr(COL_INDEX)].width = BREITE_INDEX
    ws.column_dimensions[col_ltr(COL_TASTE)].width = BREITE_TASTE
    ws.column_dimensions[col_ltr(COL_TYP)].width = BREITE_TYP
    ws.column_dimensions[col_ltr(COL_TASTE_GRP)].width = BREITE_GRP

    # LEDs & Tasten ................
    ml = max(leds.keys())
    mt = max(tasten.keys())
    ix_style = NamedStyle(_STYLE_INDEX)
    ix_style.alignment = Alignment(horizontal='center')
    ix_style.fill = PatternFill(fill_type='solid', start_color=CLR_INDEX)
    grp_b = Border(top=Side(border_style='thick', color=CLR_GROUP))
    grp_f = PatternFill(fill_type='solid', start_color=CLR_GROUP)
    grp_p = PatternFill(fill_type='solid', start_color=CLR_PORT)
#     wichtig_f = PatternFill(fill_type='solid', start_color=CLR_WICHTIG)

    # Status formats
    inp_p = PatternFill(fill_type='solid', start_color=CLR_INPUT)
    gru_p = PatternFill(fill_type='solid', start_color=CLR_GRUEN)
    ora_p = PatternFill(fill_type='solid', start_color=CLR_ORANGE)
    rot_p = PatternFill(fill_type='solid', start_color=CLR_ROT)
    wei_p = PatternFill(fill_type='solid', start_color=CLR_WEISS)
    aus_p = PatternFill(fill_type='solid', start_color=CLR_AUS)
    cfd_p = PatternFill(fill_type='solid', end_color=CLR_AUS)
#     aus_p = PatternFill(fill_type='solid', start_color=CLR_AUS)

    # Verwendung der Rahmen
    wsSet(ws, ROW_RAHMEN, COL_IGEL, TXT_RAHMEN_INFO, ix_style)
    wsSet(ws, ROW_RAHMEN + 1, COL_IGEL, f'{TXT_RAHMEN_BEZ} 1: {rahmen[0]}')
    wsSet(ws, ROW_RAHMEN + 2, COL_IGEL, f'{TXT_RAHMEN_BEZ} 2: {rahmen[1]}')

    # LED - Status - String Verarbeitung
    wsSet(ws, ROW_STATUS, COL_IGEL, TXT_LED_STRING, ix_style)
    zelle = wsSet(ws, ROW_STATUS + 1, COL_IGEL, '000100.000001.000100.010000:'*20)
    zelle.fill = inp_p
    stat_adr = col_ltr(COL_IGEL) + f'{ROW_STATUS + 1}'
    wsSet(ws, ROW_STATUS + 2, COL_IGEL, \
            f'=CONCATENATE("9",SUBSTITUTE(SUBSTITUTE({stat_adr},".",""),":",""))')
    stat_adr = f'${col_ltr(COL_IGEL)}${ROW_STATUS + 2}'

    for i in range(1 + max(ml, mt)):
        # print(f':{i} ', end='', flush=True)
        wsSet(ws, i+ROW_START, COL_INDEX, i, ix_style)    # laufender Index
        # Index je Board LED
        zelle = wsSet(ws, i+ROW_START, COL_LED_GRP, \
                       IgelTyp.LED_2.pinstart + i%IgelTyp.LED_2.pinouts)
        zelle.fill = grp_p
        # Index je Board Taste
        zelle = wsSet(ws, i+ROW_START, COL_TASTE_GRP, \
                       IgelTyp.TASTEN.pinstart + i%IgelTyp.TASTEN.pinouts)
        zelle.fill = grp_p

        # LEDs
        # - Status
        txt_led = leds.get(i, TXT_LEER)
        zelle = wsSet(ws, i+ROW_START, COL_LED_STAT, f'=MID({stat_adr},ROW(),1)')
        if TXT_LEER == txt_led:
            zelle.fill = aus_p
        elif 'FREI-' in txt_led:
            zelle.fill = gru_p
        elif 'VORSICHT' in txt_led:
            zelle.fill = ora_p
        elif any([x in txt_led for x in {'SperrM', 'gesperrt', 'HALT', 'rot'} \
                  | {'W-Melder', 'T-Melder', 'EK-Melder'}]):
            zelle.fill = rot_p
        else:   # dann isses weiß
            zelle.fill = wei_p
        zelle = wsSet(ws, i+ROW_START, COL_LED, txt_led)  # Beschreib

        # gruppieren nach Anzahl der Ports pro Board
        if i%IgelTyp.LED_2.pinouts == 0:
            zelle.border = grp_b
            zelle = wsSet(ws, i+ROW_START, COL_LED_GRP, i//IgelTyp.LED_2.pinouts)
            zelle.border = grp_b
            zelle.fill = grp_f

        # Tasten
        beschreib, typ, _ = tasten.get(i, (TXT_LEER, TastenTyp.NIX, ""))
        zelle = wsSet(ws, i+ROW_START, COL_TYP, typ.name.lower())
        zelle = wsSet(ws, i+ROW_START, COL_TASTE, beschreib)

        # gruppieren nach Anzahl der Ports pro Board
        if i%IgelTyp.TASTEN.pinouts == 0:
            zelle.border = grp_b
            zelle = wsSet(ws, i+ROW_START, COL_TASTE_GRP, i//IgelTyp.TASTEN.pinouts)
            zelle.border = grp_b
            zelle.fill = grp_f

    # Bedingte Formatierung bei Null
    regel = CellIsRule(operator='==', formula=['"0"'], stopIfTrue=True, fill=cfd_p)
    ws.conditional_formatting.add(f'A{ROW_START}:A{ROW_START+i}', regel)
#     ws.conditional_formatting.add('A:A', regel)    # TODO openpyxl braucht Zeilen :(

    # Igel .................
    curr_col = COL_IGEL
    ig_style = hd_style
    ig_style.fill = PatternFill(fill_type='solid', start_color=CLR_IGEL)

    for iname, iliste in sorted(igels.items(), key=_igel_sort):
        curr_row = 1
        igel_typ = iliste.get(_IGELS_TYP_IDX)
        wsSet(ws, curr_row, curr_col, _TXT_IGEL +"  "+ iname + \
              "  (" + igel_typ.name + ")", ig_style)
        ws.column_dimensions[col_ltr(curr_col)].width = BREITE_IGEL

        # auch leere Steckplätze zwischen belegten ausgeben; Annahme numerisch!
        for i in range(0, 1 + max(iliste.keys())):
            curr_row += 1
            wsSet(ws, curr_row, curr_col, \
                  f'{i+igel_typ.pinstart:>2} => {iliste.get(i, ("",0))[0]}')

        # nur belegte Steckplätze ausgeben
        # for k,v in sorted(iliste.items()):
            # curr_row += 1
            # wsSet(ws, curr_row, curr_col, f'{k:>3} => {v}')

        curr_col += 1

# -------------------------------------------------------------------------- #
def _steckigel_blatt(wb):
    """Listet die Anschlüsse der Steckigel in ein Excel-Blatt.
    :param wb    Excel Workbook
    """
    # pylint: disable=too-many-locals,too-many-statements
    # es braucht unterschiedliche Fonts und Stile und Daten
    # ...und besser alles an einem Platz

    # Textbausteine
    TXT1 = 'A1'
    TXT2 = 'B2'
    TXT3 = 'C3'
    TXT_KONTAKT = 'Kontakt'
    TXT_NIX = 'X'
    TXT_REIHE = 'Reihe'
    TXT_IN_REIHE = {('TAS', 0) : (TXT_REIHE, 'A', 'B', 'C'),
                    ('LED', 0) : (TXT_REIHE, 'D', 'E', 'F'),
                    ('LED', 1) : (TXT_REIHE, 'G', 'H', 'I')}

    # Formatierungen
    CLR_REIHE = '3F7AFF'
    CLR_KOPF = '95B3D7'
    CLR_NIX = 'DDAAAA'
    CLR_PIN = 'C4D79B'
    CLR_RAHMEN = '000000'

    STL_AUSR_CNTR = Alignment(horizontal='center')   # .alignment
    STL_AUSR_BESCHR = Alignment(vertical='top', wrap_text=True)        # .alignment
    STL_FILL_REIHE = PatternFill(fill_type='solid', start_color=CLR_REIHE) # .fill
    STL_FILL_KOPF = PatternFill(fill_type='solid', start_color=CLR_KOPF) # .fill
    STL_FILL_NIX = PatternFill(fill_type='solid', start_color=CLR_NIX) # .fill
    STL_FILL_PIN = PatternFill(fill_type='solid', start_color=CLR_PIN) # .fill
    STL_RHMN_RE = Border(right=Side(border_style='thin', color=CLR_RAHMEN))
    STL_RHMN_TRENN = Border(bottom=Side(border_style='double', color=CLR_RAHMEN))

    # Excel
    COL_REIHE = col_nmbr('A')
    COL_KONTAKT = COL_REIHE +1
    COL_DATA = COL_KONTAKT +1
    COL_SUM = COL_DATA + IgelTyp.anzahl_spalten()
    BREITE_REIHE = 7
    BREITE_KONTAKT = 9
    BREITE_DATEN = 14
    HOEHE_BESCHR = 44

    # Datenblattstruktur anlegen
    ws = wb.create_sheet(_BLATT_IGEL, 0)

    # Variable
    curr_row = 0

    # Summe
    zelle = wsSet(ws, 1, COL_SUM +2, \
                  f'=SUM({col_ltr(COL_SUM)}:{col_ltr(COL_SUM)})', _STYLE_UEBER)

    # Spalten formatieren
    ws.column_dimensions[col_ltr(COL_REIHE)].width = BREITE_REIHE
    ws.column_dimensions[col_ltr(COL_KONTAKT)].width = BREITE_KONTAKT
    for col in range(COL_DATA, IgelTyp.anzahl_spalten() + COL_DATA):
        ws.column_dimensions[col_ltr(col)].width = BREITE_DATEN

    # für alle Igel
    for iname, iliste in sorted(igels.items(), key=_igel_sort):

        # Parameter
        igel_typ = iliste.get(_IGELS_TYP_IDX)
        plat_divisor = igel_typ.pinouts
        # Anzahl Plätze - abzüglich der Verwaltungsinfos!!
        igel_plaetz = len(iliste.keys()) + _IGELS_ID_IDX
        style_igel = _STYLE_UEBER if igel_typ.typ == 'LED' else _STYLE_INDEX

        # Überschrift Igel
        curr_row += 1       # eine Leerzeile lassen
        ws.merge_cells(xls_range(COL_REIHE, curr_row, 1, 0))
        zelle = wsSet(ws, curr_row, COL_REIHE, \
                      _TXT_IGEL +"  "+ iname, style_igel)

        ws.merge_cells(xls_range(COL_DATA+1, curr_row, 1, 0))
        zelle = wsSet(ws, curr_row, COL_DATA+1, \
                      'Typ: ' + igel_typ.name, style_igel)

        ws.merge_cells(xls_range(COL_DATA+4, curr_row, 1, 0))
        zelle = wsSet(ws, curr_row, COL_DATA+4, \
                      f'Chain/Bus: {iliste.get(_IGELS_SEQ_IDX)}', style_igel)

        if igel_typ == IgelTyp.TASTEN:
            ws.merge_cells(xls_range(COL_DATA+7, curr_row, 1, 0))
            zelle = wsSet(ws, curr_row, COL_DATA+7, \
                          f'IOPi+ ID: 0x{iliste.get(_IGELS_ID_IDX):x}', style_igel)

        zelle = wsSet(ws, curr_row, COL_SUM -1, 'Belegt:', _STYLE_UEBER)
        zelle.alignment = Alignment(horizontal='right')
        zelle = wsSet(ws, curr_row, COL_SUM, igel_plaetz)

        # Beginn der Reihen
        for reihe in range(igel_typ.steckzeilen):
            curr_row += 1

            # Reihenkopf
            for r, t in enumerate(TXT_IN_REIHE[(igel_typ.typ, reihe)]):
                zelle = wsSet(ws, curr_row+r, COL_REIHE, t)
                zelle.alignment = STL_AUSR_CNTR
                zelle.fill = STL_FILL_REIHE

            # Kontaktkopf
            for r, t in enumerate((TXT_KONTAKT, TXT1, TXT2, TXT3)):
                zelle = wsSet(ws, curr_row+r, COL_KONTAKT, t)
                zelle.alignment = STL_AUSR_CNTR
                zelle.border = STL_RHMN_RE
                zelle.fill = STL_FILL_KOPF

            # Spaltenbelegung
            pins_pro_reihe = igel_typ.pinouts // igel_typ.steckzeilen \
                            // igel_typ.anz_kanal()
            for stecker in range(pins_pro_reihe):
                col = COL_DATA + stecker

                # Spalte 1.Kopf
                zelle = wsSet(ws, curr_row, col, \
                              f'Spalte {stecker + igel_typ.steckspalt1}')
                zelle.alignment = STL_AUSR_CNTR
                zelle.border = STL_RHMN_RE

                # Daten einfüllen
                accessnr = reihe * pins_pro_reihe + stecker
                beschr, pins = iliste.get(accessnr, ('', (TXT_NIX, )*3))

                for r, pin in enumerate(pins, 1):
                    try:
                        zelle = wsSet(ws, curr_row+r, col, \
                                      igel_typ.pinstart + pin % plat_divisor)
                    except TypeError:
                        zelle = wsSet(ws, curr_row+r, col, pin)

                    zelle.alignment = STL_AUSR_CNTR
                    zelle.border = STL_RHMN_RE

                # Beschreibung
                zelle = wsSet(ws, curr_row+4, col, beschr)
                zelle.alignment = STL_AUSR_BESCHR
                zelle.border = STL_RHMN_RE
                if beschr == '':
                    zelle.fill = STL_FILL_NIX
                else:
                    zelle.fill = STL_FILL_PIN

            ws.row_dimensions[curr_row+4].height = HOEHE_BESCHR
            curr_row += 5

        # Abgrenzung zum nächsten Igel
        for col in range(1, 2*IgelTyp.anzahl_spalten()+3):
            ws.cell(row=curr_row, column=col).border = STL_RHMN_TRENN

        curr_row += 1

# -------------------------------------------------------------------------- #
def listen_datei(quelle):
    """Listet die Daten in eine neue Excel-Datei.
    :param quelle string Name der Datenquelle
    """

    # Daten im Speicher erzeugen
    wb = Workbook()

    # das Belegungsblatt
    _belegt_blatt(wb)
    _steckigel_blatt(wb)

    # in Datei schreiben
    beleg_datei = Path(quelle).stem + _DATEI_BELEG_EXT
    try:
        wb.save(beleg_datei)
        print(f'\n-- Belegdatei {beleg_datei} geschrieben.\n')
    except PermissionError:
        print(f'\n   *** Konnte {beleg_datei} nicht schreiben - geöffnet? ***\n')

# -------------------------------------------------------------------------- #
def schreib_konfig():
    """Generieren der Konfig-Datei für die Simulation.
    :return  True wenn ein Fehler gefunden wurde.
    """
    schreib_grund()
    return schreib_aufbau()

# -------------------------------------------------------------------------- #
def schreib_grund():
    """Generieren der grundlegenden Konfig-Datei für die Simulation.
    """
    # öffne die Konfig-Datei
    k_start(_DATEI_GRUND, _BESCH_GRUND)

    # imports
    k_zeile('from enum import Enum, unique', 0)
    k_zeile('', 0)
    k_zeile('from m_common import TastenTyp', 0)
    k_zeile('', 0)

    # IOPi+ ID Reihenfolge
    k_zeile('# Rahmen die vom Relais einzuschalten sind', 0, True)
    k_zeile(f'RAHMEN_ON = {rahmen}', 0)
    k_zeile('', 0)

    # IOPi+ ID Reihenfolge
    k_zeile('# IOPi+ Adressen aus dem Daten-Excel (dezimal)', 0, True)

    z = [value[_IGELS_ID_IDX] for value in igels.values() \
               if value[_IGELS_ID_IDX] is not None]
    k_zeile(f'IOPI_ADRESSEN = {z}', 0)
    k_zeile('', 0)

    # Tasten - Klasse
    k_zeile('@unique', 0, True)
    k_zeile('class Taste(Enum):', 0)
    k_zeile('"""Alle definierten Tasten mit zugeordnetem Typ.', 1)
    k_zeile('"""', 1)

    # alle Typen der Tasten in eigenem String aufsammeln
    typ_zeilen = []
    # 0 - Strigs init
    for t in list(TastenTyp):
        typ_zeilen.append(f'# Typ: {t.name}\n')

    # das NIX muss manuell dazu
#     typ_zeilen[0] += '    TT           = ( -2, TastenTyp.NIX)    # Test- Ausgabe Schirm\n'
    typ_zeilen[0] += '    NIX          = ( -1, TastenTyp.NIX)    # keine Taste gedrückt\n'

    # Tasten durcharbeiten
    for k, v in sorted(tasten.items(), key=lambda sk: sk[1][0]):
        b, t, l = v
        typ_zeilen[t.value] += f'    {b:12} = ({k:3}, {t:17})     # {l}\n'

    # Tasten ausgeben
    for z in typ_zeilen:
        # k_zeile('', 0)      # one empty line
        k_zeile(z, 1)

    k_zeile('# eigener Konstruktor', 1)
    k_zeile('def __init__(self, kanal, typ):', 1)
    k_zeile('self.kanal = kanal    # Kanal der Input-Platine', 2)
    k_zeile('self.typ = typ        # Tastentyp (enum)', 2)
    k_zeile('', 0)

    # Melder - Klasse
    k_zeile('@unique', 0, True)
    k_zeile('class Melder(Enum):', 0)
    k_zeile('"""Alle definierten Melder mit zugeordnetem LED-Kanal.', 1)
    k_zeile('"""', 1)

    # Melder nach Name geordnet
    for k, v in sorted(melder.items()):
        k_zeile(f'{k:7} = (' + ', '.join(str(s) for s in v[:-1]) \
                + f')      # {v[-1]}', 1)

    k_zeile('', 0)
    k_ende()

# -------------------------------------------------------------------------- #
def schreib_aufbau():
    """Generieren der aufbauenden Konfig-Datei für die Simulation.
    """
    # öffne die Konfig-Datei
    k_start(_DATEI_AUFBAU, _BESCH_AUFBAU)

    # imports
    k_zeile('from c_gleis import Gleis', 0)
    k_zeile('from c_fahrstrasse import Fahrstrasse', 0)
    k_zeile('from c_weiche_fern import FernWeiche', 0)
    k_zeile('from c_weiche_orts import OrtsWeiche', 0)
    for datei, klasse, _, _ in _SIGNAL_KLASSEN.values():
        k_zeile(f'from {datei} import {klasse}', 0)
    k_zeile('from c_melder import ' \
            + ' ,'.join(x for x in set(v[0] for v in _MELDER_KLASSEN.values())), 0)
    k_zeile('from daten_basis import Taste', 0)
    k_zeile('import m_basis', 0)
    k_zeile('', 0)

    # ---------- init()
    k_zeile('def init():', 0, True)
#     k_zeile('def init(simuliert):', 0, True)
    k_zeile('"""Initialisieren der Daten.', 1)
#     k_zeile(':param  simuliert: bool  True wenn mit Elektronik simuliert wird', 1)
    k_zeile('"""', 1)
    k_zeile('', 0)

    # Konstante
    k_zeile('# Basis-Konstante', 1)
    k_zeile(f'm_basis.max_led_kanal = {max(leds.keys())}', 1)
    k_zeile(f'm_basis.max_tast_kanal = {max(tasten.keys())}', 1)
    k_zeile('', 0)

    # ---------- init_elements()
    k_zeile('def init_elements():', 0, True)
    k_zeile('"""Erzeugen der einzelnen Elemente des Stellwerks.', 1)
    k_zeile('"""', 1)

    # Gleisabschnitte
    k_zeile('', 0)
    k_zeile('# Gleisabschnitte', 1)
    k_zeile(f'm_basis.abschnitte = Gleis( \\', 1)
    k_zeile(f'{gleis})'.replace(", '", ", \\\n             '"), 3)

    # mehr
    _schreib_weichen()          # Weichen
    _schreib_spezi_melder()     # Spezialmelder
    fehler = _schreib_signale() # Signale
    _schreib_fahrstr()          # Fahrstrassen

    # Ende
    k_zeile('', 0)
    k_ende()

    return fehler

# -------------------------------------------------------------------------- #
def _schreib_weichen():
    """Generieren des Weichen-Teils der Konfig-Datei.
    """
    k_zeile('', 0)
    k_zeile('# Weichen', 1)
    for k, v in sorted(weichen.items()):
        typ, init_links, led_list = v

        k_zeile(f"m_basis.elemente[Taste.{k}] = \\", 1)

        if typ == 'o':
            # ortsbedient ignoriert init_links
            k_zeile(f"OrtsWeiche('{k}', (" \
                    + ', '.join(str(s) for s in led_list) + '))', 3)
        if typ == 'f':
            # fernbedient
            k_zeile(f"FernWeiche('{k}', (" \
                    + ', '.join(str(s) for s in led_list) + f'), {init_links})', 3)

# -------------------------------------------------------------------------- #
def _schreib_spezi_melder():
    """Generieren des Spezial-Melder-Teils der Konfig-Datei.
    """
    k_zeile('', 0)
    k_zeile('# --- Spezialmelder', 1)

    for k, v in sorted(spezi_melder.items()):
        bana, ka_li, ka_re, txt_lng = v
        k_zeile(f'# {txt_lng}', 1)
        txt = f"m_basis.elemente['{k}'] = {_MELDER_KLASSEN[bana][0]}('{k}', {ka_li}"
        if ka_re is not None:
            txt += f', {ka_re}'
        k_zeile(f'{txt})', 1)

# -------------------------------------------------------------------------- #
def _schreib_signale():
    """Generieren des Signal-Teils der Konfig-Datei.
    :returns  True falls noch ein Fehler aufgetreten ist
    """
    # pylint: disable=too-many-branches,too-many-statements
    # manchmal braucht es eben mehr und ist nicht sinnvoll unterteilbar
    fehler = False

    k_zeile('', 0)
    k_zeile('# --- Signale', 1)

    for tt in list(TastenTyp):

        # überspringe die Typen die keine Signale sind
        if tt in (TastenTyp.NIX, TastenTyp.WEICHE, TastenTyp.GRUPPE, TastenTyp.DOKU):
            continue

        # alles andere sollte Signal sein
        k_zeile('', 0)
        k_zeile(f'# {tt.name}', 1)

        # die langen Einfahrten sind aber speziell!
        if tt == TastenTyp.AS_LANG:
            for lange, kurze in sorted(lange_as.items()):
                k_zeile(f'm_basis.elemente[Taste.{lange}] = m_basis.elemente[Taste.{kurze}]', 1)
            continue

        # selektiere nach TastenTyp, sortiere nach Bezeichnung Taste
        for _, v in sorted([x for x in tasten.items() if x[1][1] == tt], \
                           key=lambda sk: sk[1][0]):
            b, _, _ = v
            try:
                v_typ, bhf, sname, v_led = signale[b]
            except KeyError:
                k_zeile('** Prüfung fehlgeschlagen (kein Signal für Taste) **\n', \
                        3, True)
                k_ende()
                raise KeyError('wirklich unerwarteter Fehler: ' \
                               + f'kein Signal für Taste {b} ?!')

            # Beginn Ausgabe der Daten - Zeile 1
            k_zeile(f'm_basis.elemente[Taste.{b}] = \\', 1)

            # Zeile 2 - sind Daten für den Signaltyp vorhanden?
            try:
                sig_info = _SIGNAL_KLASSEN[v_typ]
            except KeyError:
                fehler = True
                k_zeile('** Prüfung fehlgeschlagen (Klassendaten) **\n', 3, True)
                print('wirklich unerwarteter Fehler: ' \
                     + f'keine Klasse für Signaltyp {tt.name} ?!\n' \
                     + '(Ergänze Daten der _SIGNAL_KLASSEN!)', file=stderr)

            # Klassenname, Signaltaste
            txt = f'{sig_info[1]}' + f"('{b}', ("
            # Liste der LEDs
            txt += ', '.join(str(s) for s in v_led) + ')'

            # Falls weitere Informationen vorhanden, dann Zeile teilen
            if sig_info[2] or sig_info[3]:
                txt += ' \\'
                k_zeile(txt, 3)
                txt = ''        # textpuffer leeren
            else:
                txt += ')'
                k_zeile(txt, 3)
                continue

            # wenns ein Vorsignal geben sollte
            if sig_info[2]:
                try:
                    vs_key = sname[0].lower()
                    txt += f", '{vorsignale[bhf][vs_key]}'"
                except KeyError:
                    fehler = True
                    k_zeile(f'** Prüfung fehlgeschlagen (kein Vorsignal {vs_key}) **\n', \
                            3, True)
                    print(f'** Kein Vorsignal {vs_key} gefunden für Signal {b}\n' \
                           + '(Prüfe Daten im XLSX!) **')

            # wenns einen VGRM gibt
            if sig_info[3]:
                vgrm = _mach_name(bhf, 'VGrM_' + sname[0])
                try:
                    _ = spezi_melder[vgrm]
                    txt += f", '{vgrm}'"
                except KeyError:
                    fehler = True
                    k_zeile(f'** Prüfung fehlgeschlagen (kein {vgrm}) **\n', \
                            3, True)
                    print(f'** Kein Versch.Grundst.Melder {vgrm} gefunden für Signal {b}.')
                    print('(Prüfe Daten im XLSX!) **')
                    print(f'vorhanden: {" : ".join(spezi_melder.keys())}')

            txt += ')'
            k_zeile(txt, 5)

    return fehler

# -------------------------------------------------------------------------- #
def _schreib_fahrstr():
    """Generieren des Fahrstrassen-Teils der Konfig-Datei.
    """
    # Ausgabe der Fahrstrassen
    k_zeile('', 0)
    k_zeile('# --- Fahrstrassen', 1)
    k_zeile('# pylint: disable=line-too-long', 1)
    k_zeile('# die Daten können umfangreich sein', 1)

    for k, v in sorted(fs.items()):
        k_zeile(f"m_basis.fahrstrassen[{k}] = Fahrstrasse \\", 1)
        k_zeile(f'{v}'.replace(', {', ', \\\n' + ' '*13 + '{'), 3)
        k_zeile('', 0)

    k_zeile('# pylint: enable=line-too-long', 1)

# -------------------------------------------------------------------------- #
def testausgabe():
    """special assignment"""

#     print(f'Igels: {igels}')
#     print(f'Lange AS: {lange_as}')
#     print(f'LEDs: {leds}')
#     print(f'Melder: {melder}')
#     print(f'spezi-Melder: {spezi_melder}')
#     print(f'Signale: {signale}')
#     print(f'Tasten: {tasten}')
#     print(f'Vorsignale: {vorsignale}')
    print(f'Weichen: {weichen}')

# ------------------------------------------------------------- Ende Gelände #

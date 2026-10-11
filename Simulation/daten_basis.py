"""
Definition der grundlegenden Daten, auf denen andere Daten aufbauen.
"""
# ---------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# ../BAC2_Simulation/src/daten_basis.py
#
# generiert nach Prüfung am 2022-07-19 um 21:49:15
# ---------------------------------------------------------------------------- #
# pylint: disable=bad-whitespace
# Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht

from enum import Enum, unique

from m_common import TastenTyp

# ---------------------------------------------------------------------------- #
# Rahmen die vom Relais einzuschalten sind
RAHMEN_ON = (True, False)

# ---------------------------------------------------------------------------- #
# IOPi+ Adressen aus dem Daten-Excel (dezimal)
IOPI_ADRESSEN = [32, 33, 34, 35]

# ---------------------------------------------------------------------------- #
@unique
class Taste(Enum):
    """Alle definierten Tasten mit zugeordnetem Typ.
    """
    # Typ: NIX
    NIX          = ( -1, TastenTyp.NIX)    # keine Taste gedrückt

    # Typ: WEICHE
    WT_Ad_006    = ( 15, TastenTyp.WEICHE )     # Taste FernW Ad:  6
    WT_Ad_031    = ( 46, TastenTyp.WEICHE )     # Taste OrtsW Ad: 31
    WT_Ad_053    = ( 47, TastenTyp.WEICHE )     # Taste FernW Ad: 53

    # Typ: VERSCHUB
    ST_Ad_V3     = (  3, TastenTyp.VERSCHUB)     # Ad - Verschubsignal V3
    ST_Ad_V55    = ( 35, TastenTyp.VERSCHUB)     # Ad - Verschubsignal V55

    # Typ: VORSIG
    ST_Ad_a      = (  0, TastenTyp.VORSIG )     # Einfahr-Vorsignal a für Ad
    ST_Ad_z      = ( 32, TastenTyp.VORSIG )     # Einfahr-Vorsignal z für Ad

    # Typ: ES
    ST_Ad_A      = (  2, TastenTyp.ES     )     # Einfahrt in Ad A+r
    ST_Ad_Z      = ( 34, TastenTyp.ES     )     # Einfahrt in Ad Z+h

    # Typ: AS
    ST_Ad_H1_krz = (  4, TastenTyp.AS     )     # AusfahrtSignal in Ad H1 kurz
    ST_Ad_H3     = (  6, TastenTyp.AS     )     # AusfahrtSignal in Ad H3 kurz
    ST_Ad_R1_krz = ( 38, TastenTyp.AS     )     # AusfahrtSignal in Ad R1 kurz
    ST_Ad_R3     = ( 36, TastenTyp.AS     )     # AusfahrtSignal in Ad R3 kurz

    # Typ: AS_LANG
    ST_Ad_H1_lng = (  5, TastenTyp.AS_LANG)     # AusfahrtSignal in Ad H1 lang
    ST_Ad_R1_lng = ( 37, TastenTyp.AS_LANG)     # AusfahrtSignal in Ad R1 lang

    # Typ: STRECKE
    ST_Ad_nachBo = ( 33, TastenTyp.STRECKE)     # von Ad auf Strecke nachBo
    ST_Ad_nachCd = (  1, TastenTyp.STRECKE)     # von Ad auf Strecke nachCd

    # Typ: GRUPPE
    BGT          = ( 21, TastenTyp.GRUPPE )     # Blockgruppentaste
    BlÜT         = ( 25, TastenTyp.GRUPPE )     # Blinkspannungsüberprüftaste
    Du           = ( 56, TastenTyp.GRUPPE )     # Dunkeltaste
    EKEGT        = ( 19, TastenTyp.GRUPPE )     # EK-Einschaltgruppentaste
    EspT         = ( 27, TastenTyp.GRUPPE )     # Entsperrtaste
    HaGT         = ( 24, TastenTyp.GRUPPE )     # Haltgruppentaste
    He           = ( 57, TastenTyp.GRUPPE )     # Helltaste
    NFT          = ( 49, TastenTyp.GRUPPE )     # Nahstellbetriebsfreigabetaste
    NRT          = ( 50, TastenTyp.GRUPPE )     # Nahstellbetriebsrücknahmetaste
    SpT          = ( 26, TastenTyp.GRUPPE )     # Sperrtaste
    Stop         = ( 54, TastenTyp.GRUPPE )     # Stoptaste
    VGT          = ( 23, TastenTyp.GRUPPE )     # Verschubsignalgruppentaste
    WGT          = ( 52, TastenTyp.GRUPPE )     # Weichengruppentaste
    WUT          = ( 28, TastenTyp.GRUPPE )     # Weckerunterbrechertaste

    # Typ: DOKU
    EKGrT        = ( 18, TastenTyp.DOKU   )     # EK-Grundstellungstaste
    EKÜT         = ( 17, TastenTyp.DOKU   )     # EK-Überbrückungstaste
    ErsGT        = ( 22, TastenTyp.DOKU   )     # Ersatzsignalgruppentaste
    FHT          = ( 53, TastenTyp.DOKU   )     # Fahrstraßenhilfsauflösetaste
    NHT          = ( 48, TastenTyp.DOKU   )     # Nahstellbetriebshilfsrücknahmetaste
    WHT          = ( 51, TastenTyp.DOKU   )     # Weichenhilfstaste

    # eigener Konstruktor
    def __init__(self, kanal, typ):
        self.kanal = kanal    # Kanal der Input-Platine
        self.typ = typ        # Tastentyp (enum)

# ---------------------------------------------------------------------------- #
@unique
class Melder(Enum):
    """Alle definierten Melder mit zugeordnetem LED-Kanal.
    """
    BlÜM    = (32, 44)      # Blinkspannungs-Überprüfungsmelder
    EK      = (35, 47)      # Eisenbahnkreuzungs-Störmelder
    N       = (71, None)      # Netzmelder
    T       = (34, 46)      # Tastenstörmelder
    W       = (33, 45)      # Weichenstörmelder

# ------------------------------------------------------------- Ende Gelände #

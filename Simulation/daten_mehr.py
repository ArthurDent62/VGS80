"""
Definition jener Daten welche die Basis-Daten verwenden.
"""
# ---------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# ../BAC2_Simulation/src/daten_mehr.py
#
# generiert nach Prüfung am 2022-07-19 um 21:49:15
# ---------------------------------------------------------------------------- #
# pylint: disable=bad-whitespace
# Hier wird die Lesbarkeit mit mehr Leerzeichen erhöht

from c_gleis import Gleis
from c_fahrstrasse import Fahrstrasse
from c_weiche_fern import FernWeiche
from c_weiche_orts import OrtsWeiche
from c_signal_versch import VerschubSignal
from c_signal_evs import EinfahrVorsignal
from c_signal_es import EinfahrSignal
from c_signal_as import Ausfahr_VerschubSignal
from c_signal_strecke import Strecke
from c_melder import VGrM
from daten_basis import Taste
import m_basis

# ---------------------------------------------------------------------------- #
def init():
    """Initialisieren der Daten.
    """

    # Basis-Konstante
    m_basis.max_led_kanal = 143
    m_basis.max_tast_kanal = 57

# ---------------------------------------------------------------------------- #
def init_elements():
    """Erzeugen der einzelnen Elemente des Stellwerks.
    """

    # Gleisabschnitte
    m_basis.abschnitte = Gleis( \
            {'G101_Ad': ({120}, {132}), \
             'G201_Ad': ({121, 97}, {109, 133}), \
             'G301_Ad': ({122, 98}, {110, 134}), \
             'G401_Ad': ({123}, {135}), \
             'G403_Ad': ({100, 124}, {136, 112}), \
             'G501_Ad': ({96, 101, 125, 103}, {137, 115, 108, 113}), \
             'G503_Ad': ({102, 126}, {138, 114}), \
             'G601_Ad': ({127}, {139}), \
             'G603_Ad': ({128, 104}, {116, 140}), \
             'G701_Ad': ({129, 105}, {117, 141}), \
             'G801_Ad': ({130, 106}, {118, 142}), \
             'G901_Ad': ({131}, {143})})

    # Weichen
    m_basis.elemente[Taste.WT_Ad_006] = \
            FernWeiche('WT_Ad_006', (29, 41, 30, 42, 31, 43), False)
    m_basis.elemente[Taste.WT_Ad_031] = \
            OrtsWeiche('WT_Ad_031', (80, 92, 81, 93, 65))
    m_basis.elemente[Taste.WT_Ad_053] = \
            FernWeiche('WT_Ad_053', (77, 89, 78, 90, 79, 91), True)

    # --- Spezialmelder
    # Verschubsignalgrundstellungsmelder H in Bf. Ad
    m_basis.elemente['Ad_VGrM_H'] = VGrM('Ad_VGrM_H', 16)
    # Verschubsignalgrundstellungsmelder R in Bf. Ad
    m_basis.elemente['Ad_VGrM_R'] = VGrM('Ad_VGrM_R', 64)

    # --- Signale

    # VERSCHUB
    m_basis.elemente[Taste.ST_Ad_V3] = \
            VerschubSignal('ST_Ad_V3', (26, 38))
    m_basis.elemente[Taste.ST_Ad_V55] = \
            VerschubSignal('ST_Ad_V55', (74, 86))

    # VORSIG
    m_basis.elemente[Taste.ST_Ad_a] = \
            EinfahrVorsignal('ST_Ad_a', (0, 1, 2))
    m_basis.elemente[Taste.ST_Ad_z] = \
            EinfahrVorsignal('ST_Ad_z', (48, 49, 50))

    # ES
    m_basis.elemente[Taste.ST_Ad_A] = \
            EinfahrSignal('ST_Ad_A', (24, 36, 25, 37, 5, 6) \
                    , 'ST_Ad_a')
    m_basis.elemente[Taste.ST_Ad_Z] = \
            EinfahrSignal('ST_Ad_Z', (72, 84, 73, 85, 53, 54) \
                    , 'ST_Ad_z')

    # AS
    m_basis.elemente[Taste.ST_Ad_H1_krz] = \
            Ausfahr_VerschubSignal('ST_Ad_H1_krz', (7, 27, 39, 8, 9, 11) \
                    , 'Ad_VGrM_H')
    m_basis.elemente[Taste.ST_Ad_H3] = \
            Ausfahr_VerschubSignal('ST_Ad_H3', (12, 28, 40, 13, 14, 15) \
                    , 'Ad_VGrM_H')
    m_basis.elemente[Taste.ST_Ad_R1_krz] = \
            Ausfahr_VerschubSignal('ST_Ad_R1_krz', (60, 76, 88, 61, 62, 63) \
                    , 'Ad_VGrM_R')
    m_basis.elemente[Taste.ST_Ad_R3] = \
            Ausfahr_VerschubSignal('ST_Ad_R3', (55, 75, 87, 56, 57, 59) \
                    , 'Ad_VGrM_R')

    # AS_LANG
    m_basis.elemente[Taste.ST_Ad_H1_lng] = m_basis.elemente[Taste.ST_Ad_H1_krz]
    m_basis.elemente[Taste.ST_Ad_R1_lng] = m_basis.elemente[Taste.ST_Ad_R1_krz]

    # STRECKE
    m_basis.elemente[Taste.ST_Ad_nachBo] = \
            Strecke('ST_Ad_nachBo', (51, 52))
    m_basis.elemente[Taste.ST_Ad_nachCd] = \
            Strecke('ST_Ad_nachCd', (3, 4))

    # --- Fahrstrassen
    # pylint: disable=line-too-long
    # die Daten können umfangreich sein
    m_basis.fahrstrassen[('ST_Ad_A', 'ST_Ad_R1_krz')] = Fahrstrasse \
            (('ST_Ad_A', 'ST_Ad_R1_krz'), \
             {'WT_Ad_006': False}, \
             {'ST_Ad_H1_krz', 'ST_Ad_V3', 'ST_Ad_V55', 'ST_Ad_H3'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_H1_krz', 'ST_Ad_nachCd'), ('ST_Ad_H3', 'ST_Ad_nachCd'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H1_krz')}, \
             {'G501_Ad', 'G401_Ad', 'G301_Ad'}, 'G401_Ad')

    m_basis.fahrstrassen[('ST_Ad_A', 'ST_Ad_R1_lng')] = Fahrstrasse \
            (('ST_Ad_A', 'ST_Ad_R1_lng'), \
             {'WT_Ad_006': False, 'WT_Ad_053': True, 'WT_Ad_031': True}, \
             {'ST_Ad_H1_krz', 'ST_Ad_V3', 'ST_Ad_V55', 'ST_Ad_H3'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_H3', 'ST_Ad_nachCd'), ('ST_Ad_H1_krz', 'ST_Ad_nachCd'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_Z', 'ST_Ad_H1_krz'), ('ST_Ad_Z', 'ST_Ad_H3'), ('ST_Ad_R3', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G501_Ad', 'G401_Ad', 'G301_Ad'}, 'G401_Ad')

    m_basis.fahrstrassen[('ST_Ad_A', 'ST_Ad_R3')] = Fahrstrasse \
            (('ST_Ad_A', 'ST_Ad_R3'), \
             {'WT_Ad_006': True, 'WT_Ad_031': True}, \
             {'ST_Ad_H1_krz', 'ST_Ad_V3', 'ST_Ad_V55', 'ST_Ad_H3'}, set(), \
             {('ST_Ad_H1_krz', 'ST_Ad_nachCd'), ('ST_Ad_H3', 'ST_Ad_nachCd'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H3'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G301_Ad', 'G403_Ad', 'G503_Ad'}, 'G403_Ad')

    m_basis.fahrstrassen[('ST_Ad_H1_krz', 'ST_Ad_nachCd')] = Fahrstrasse \
            (('ST_Ad_H1_krz', 'ST_Ad_nachCd'), \
             {'WT_Ad_006': False}, \
             {'ST_Ad_H1_krz', 'ST_Ad_V3', 'ST_Ad_V55', 'ST_Ad_H3'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_H3', 'ST_Ad_nachCd'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G401_Ad', 'G301_Ad'}, 'G301_Ad')

    m_basis.fahrstrassen[('ST_Ad_H3', 'ST_Ad_nachCd')] = Fahrstrasse \
            (('ST_Ad_H3', 'ST_Ad_nachCd'), \
             {'WT_Ad_006': True, 'WT_Ad_031': True}, \
             {'ST_Ad_H1_krz', 'ST_Ad_V3', 'ST_Ad_V55', 'ST_Ad_H3'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_H1_krz', 'ST_Ad_nachCd'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G301_Ad', 'G403_Ad'}, 'G301_Ad')

    m_basis.fahrstrassen[('ST_Ad_R1_krz', 'ST_Ad_nachBo')] = Fahrstrasse \
            (('ST_Ad_R1_krz', 'ST_Ad_nachBo'), \
             {'WT_Ad_053': True, 'WT_Ad_031': True}, \
             {'ST_Ad_R3', 'ST_Ad_V3', 'ST_Ad_R1_krz', 'ST_Ad_V55'}, set(), \
             {('ST_Ad_Z', 'ST_Ad_H3'), ('ST_Ad_Z', 'ST_Ad_H1_krz'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_R3', 'ST_Ad_nachBo')}, \
             {'G601_Ad', 'G701_Ad'}, 'G701_Ad')

    m_basis.fahrstrassen[('ST_Ad_R3', 'ST_Ad_nachBo')] = Fahrstrasse \
            (('ST_Ad_R3', 'ST_Ad_nachBo'), \
             {'WT_Ad_053': False, 'WT_Ad_031': True}, \
             {'ST_Ad_R3', 'ST_Ad_V3', 'ST_Ad_R1_krz', 'ST_Ad_V55'}, set(), \
             {('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_R1_krz', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H1_krz'), ('ST_Ad_Z', 'ST_Ad_H3')}, \
             {'G603_Ad', 'G701_Ad'}, 'G701_Ad')

    m_basis.fahrstrassen[('ST_Ad_Z', 'ST_Ad_H1_krz')] = Fahrstrasse \
            (('ST_Ad_Z', 'ST_Ad_H1_krz'), \
             {'WT_Ad_053': True, 'WT_Ad_031': True}, \
             {'ST_Ad_R3', 'ST_Ad_V3', 'ST_Ad_R1_krz', 'ST_Ad_V55'}, set(), \
             {('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_R1_krz', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H3'), ('ST_Ad_R3', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G501_Ad', 'G601_Ad', 'G701_Ad'}, 'G601_Ad')

    m_basis.fahrstrassen[('ST_Ad_Z', 'ST_Ad_H1_lng')] = Fahrstrasse \
            (('ST_Ad_Z', 'ST_Ad_H1_lng'), \
             {'WT_Ad_006': False, 'WT_Ad_053': True, 'WT_Ad_031': True}, \
             {'ST_Ad_R3', 'ST_Ad_V3', 'ST_Ad_R1_krz', 'ST_Ad_V55'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_H3', 'ST_Ad_nachCd'), ('ST_Ad_R1_krz', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H1_krz'), ('ST_Ad_Z', 'ST_Ad_H3'), ('ST_Ad_R3', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_krz')}, \
             {'G501_Ad', 'G601_Ad', 'G701_Ad'}, 'G601_Ad')

    m_basis.fahrstrassen[('ST_Ad_Z', 'ST_Ad_H3')] = Fahrstrasse \
            (('ST_Ad_Z', 'ST_Ad_H3'), \
             {'WT_Ad_053': False, 'WT_Ad_031': True}, \
             {'ST_Ad_R3', 'ST_Ad_V3', 'ST_Ad_R1_krz', 'ST_Ad_V55'}, set(), \
             {('ST_Ad_A', 'ST_Ad_R3'), ('ST_Ad_Z', 'ST_Ad_H1_lng'), ('ST_Ad_R1_krz', 'ST_Ad_nachBo'), ('ST_Ad_A', 'ST_Ad_R1_lng'), ('ST_Ad_Z', 'ST_Ad_H1_krz'), ('ST_Ad_R3', 'ST_Ad_nachBo')}, \
             {'G503_Ad', 'G603_Ad', 'G701_Ad'}, 'G603_Ad')

    # pylint: enable=line-too-long

# ------------------------------------------------------------- Ende Gelände #

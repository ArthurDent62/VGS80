"""
Automatic - zum testen der automatischen Ausführung beim Booten des Pi.
Schaltet (derzeit nur) die LEDs aus da die blöderweise immer gleich an sind.
"""
# -------------------------------------------------------------------------- #
# (c) 2019 Walter Haschka
#
# Versionen
# 0.0 2019-02-04 wh Simulations-Programm begonnen
# -------------------------------------------------------------------------- #

import argparse

import daten_mehr
from m_ausgaben import MeldeTyp as MTyp, melde, setze_proto_grad
import m_pult_ausgabe

# ----------------------------------------------------- Konstante definieren #
TXT_BILD = 'zusätzliche Bedienung am Bildschirm'

# ------------------------------------------------------ Variable definieren #

# -------------------------------------------------- Argument(e) analysieren #
parser = argparse.ArgumentParser(description= \
    f'Startet die Stellwerk-Simulation VGS80.')
parser.add_argument('-b', '--bildschirm', dest='bild', action='store_true', \
    help=TXT_BILD)
args = parser.parse_args()

setze_proto_grad(MTyp.INFO)       # je nach Bedarf
melde(MTyp.IMMER, '----- Simulation gestartet')
if args.bild:
    melde(MTyp.FEHLER, f'{TXT_BILD} noch nicht implementiert!')

# -------------------------------------------------------------- Lichter aus #
daten_mehr.init()
m_pult_ausgabe.init(True)

# ------------------------------------------------------------- Ende Gelände #

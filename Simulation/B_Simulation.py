"""
Schritt B - die eigentliche Simulation des VGS80:
Einlesen der Tasten, prüfen der Eingabe, ändern des Zustands,
entsprechende Stellung der Melder.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-04 wh Simulations-Programm begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

import argparse

from m_common import TastenTyp
from daten_basis import Taste
import daten_mehr
from m_ausgaben import MeldeTyp as MTyp, melde, setze_proto_grad, setze_print_grad
import m_basis
import m_pult_eingabe
import m_pult_ausgabe

# from watcher import watcher

# ----------------------------------------------------- Konstante definieren #
TXT_BILD = 'zusätzliche Bedienung am Bildschirm'
TXT_PLATIN_EIN = 'Platinen der Eingabe (Tasten) verwenden'
TXT_PLATIN_AUS = 'LEDs für die Ausgabe verwenden'

# ------------------------------------------------------ Variable definieren #
weitermachen = True         # False: Simulation wird beendet

# -------------------------------------------------- Argument(e) analysieren #
parser = argparse.ArgumentParser(description= \
    f'Startet die Stellwerk-Simulation VGS80.')
parser.add_argument('-e', '--eingabe', dest='ein_echt', action='store_true', \
    help=TXT_PLATIN_EIN)
parser.add_argument('-a', '--ausgabe', dest='aus_echt', action='store_true', \
    help=TXT_PLATIN_AUS)
parser.add_argument('-b', '--bildschirm', dest='bild', action='store_true', \
    help=TXT_BILD)
args = parser.parse_args()

print_grad = MTyp.INFO
setze_print_grad(print_grad)        # je nach Bedarf
setze_proto_grad(MTyp.WARN)         # je nach Bedarf
melde(MTyp.IMMER, '----- Simulation gestartet')
melde(MTyp.INFO, f'{TXT_PLATIN_EIN}? {args.ein_echt}')
melde(MTyp.INFO, f'{TXT_PLATIN_AUS}? {args.aus_echt}')
if args.bild:
    melde(MTyp.FEHLER, f'{TXT_BILD} noch nicht implementiert!')

# -------------------------------------------------------------- Vorbereiten #
daten_mehr.init()
m_pult_ausgabe.init(args.aus_echt)
m_pult_eingabe.init(args.ein_echt)

# andere Ausgaben sperren, Elemente initialisieren
m_pult_ausgabe.aendern_erlaubt()
daten_mehr.init_elements()

############## bei Fehlersuche ################
# watcher(m_basis.elemente[Taste.ST_Ad_a], '_zustand', 'watcher.log')

# eigene Änderungen rausschreiben, andere Ausgaben wieder zulassen
m_pult_ausgabe.aendern_fertig()

# ******************************************************** Anfang * Methoden #

# -------------------------------------------------------------------------- #
def tasten_verarbeiten(t0, t1):
    """Abfragen der Eingabe-Platinen und abarbeiten der gedrückten Tasten.
    :param t0  Taste  die höherwertige Taste
    :param t1  Taste  die niederwertige Taste
    """
    if t0 == Taste.NIX:
        return          # keine Taste gedrückt, mir seind fertig

    # ------------------------------------------------------ einzelne Tasten #
    if t1 == Taste.NIX:
        # Tasten die einzeln wirken
        if t0 == Taste.Du:
            m_pult_ausgabe.heller(False)
        elif t0 == Taste.He:
            m_pult_ausgabe.heller(True)
        elif t0 == Taste.BlÜT:
            m_pult_ausgabe.bluem_ein()
        elif t0 == Taste.Stop:
            global weitermachen
            weitermachen = False

        return          # keine andere Taste ist einzeln sinnhaft, also fertig

    # -------------------------------------- dokumentationspflichtige Tasten #
    if t0.typ == TastenTyp.DOKU:
        # TODO_Phase3 entsprechende Aktion hier setzen (Druck/Alarm o.dgl.)
        melde(MTyp.INFO, f'  ** Doku-pflichtig: {t0.name} **')

    # ----------------------------------------------------- paarweise Tasten #
    try:
        elem = m_basis.elemente[t1]
    except KeyError:
        # kein passendes Element vorhanden
        melde(MTyp.FEHLER, f'kein Pult-Element gefunden für: {t1}')
        return      # da kömma nix tun

    # 'elem' ist als Variable notwendig, sonst würden während 'verarbeite' ALLE
    # auftretenden KeyError in obigem try abgefangen und nicht gemeldet werden!
    elem.verarbeite(t0)

    # ggf. Status ausgeben
    m_pult_ausgabe.liste_leds(MTyp.INFO)
    m_basis.show_all_stati(MTyp.DEBUG)

# ********************************************************** Ende * Methoden #


# ---------------------------------------------------------------- ausführen #
# ausführen bis Strg-C oder die Stop-Taste am Pult gedrückt wird
try:
    while weitermachen:
#         m_pult_ausgabe.liste_leds()       # B4 prod debug löschen ++++++++++++
#         m_basis.show_all_stati()          # B4 prod debug löschen ++++++++++++
        # ausführen der Routinen
        taste0, taste1 = m_pult_eingabe.gedrueckte_tasten()
        melde(MTyp.INFO, f'Taste 0 = {taste0}, Taste 1 = {taste1}')

        # während der Verarbeitung darf niemand stören!
        m_pult_ausgabe.aendern_erlaubt()
        tasten_verarbeiten(taste0, taste1)
        m_pult_ausgabe.aendern_fertig()

except (KeyboardInterrupt, EOFError):
    pass

# Abschluss - alles abschalten
melde(MTyp.IMMER, '----- Simulation endet!')
# m_pult_eingabe.abschalten()
m_pult_ausgabe.abschalten()

# ------------------------------------------------------------- Ende Gelände #

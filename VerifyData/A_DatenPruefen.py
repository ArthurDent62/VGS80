"""
Schritt A für die Simulation des VGS80:
Prüfen der Daten in der Excel-Datei, und
Erstellung der Konfigurations-Dateien.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2022 Walter Haschka
#
# Versionen
# 0.0 2019-02-01 wh Prüfprogramm begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

import argparse
import sys
from openpyxl import load_workbook

import m_daten
import m_igel
import m_sonstige
import m_weiche
import m_signal
import m_gleis
import m_fahrstrasse

# ----------------------------------------------------- Konstante definieren #
# Dateien
EINGABE_DATEI = r'VGS80_Daten.xlsx'

# Exit Codes
EXIT_OK = 0                     # Alles gut!
EXIT_DATA_ERROR = 1             # Fehler in Daten gefunden
EXIT_DATA_INCONSISTENCE = 4     # Fehler erst bei Ausgabe am Ende gefunden

# -------------------------------------------------- Argument(e) analysieren #
parser = argparse.ArgumentParser(description= \
    f'Prüfen der Daten aus {EINGABE_DATEI} für die Stellwerk-Simulation VGS80.')
parser.add_argument('-b', '--belegung', dest='beleg_datei', action='store_true', \
    help='Belegungs-Dateien erstellen')
parser.add_argument('-d', '--datei', dest='quelle', action='store', \
                    default=EINGABE_DATEI, \
    help=f'Verwende Quelle als Eingabedatei (ersetzt {EINGABE_DATEI})')
parser.add_argument('-k', '--konfig', dest='konf_datei', action='store_true', \
    help='auch Konfigurations-Dateien erstellen')
parser.add_argument('-t', '--testen', dest='testlauf', action='store_true', \
    help='Testlauf durchführen (je nachdem was getestet wird...)')
parser.add_argument('-z', '--zeigen', dest='ergeb_zeigen', action='store_true', \
    help='Prüfungsergebnisse am Bildschirm ausgeben')
args = parser.parse_args()

if args.konf_datei and args.beleg_datei:
    print('\n++ prüfen, Konfigurations- und Belegungs-Dateien erzeugen\n')
elif args.konf_datei:
    print('\n-+ prüfen, NUR Konfigurations-Dateien generieren\n')
elif args.beleg_datei:
    print('\n+- prüfen, NUR Belegungs-Dateien generieren\n')
else:
    print('\n-- NUR prüfen, keine Dateien generieren\n')
if args.ergeb_zeigen:
    print('   + Ergebnisse am Bildschirm anzeigen')

# ------------------------------ Excel öffnen und vorhandene Tabellen prüfen #
print(f'-- prüfe Datei "{args.quelle}"')
fehler = False
wb = load_workbook(args.quelle, data_only=True)

print()     # Leerzeile nach den openpyxl Fehlermeldungen
fehler |= m_igel.pruefe(wb)
fehler |= m_weiche.pruefe(wb)
fehler |= m_signal.pruefe(wb)
fehler |= m_gleis.pruefe(wb)
fehler |= m_fahrstrasse.pruefe(wb)
fehler |= m_sonstige.pruefe(wb)

# TODO_Phase3 Streckenblock, Speichermelder +++++++++++++++++++++

# -------------------------------------------------------- Ergebnisse zeigen #
if args.beleg_datei:
    # in Dateien schreiben
    m_daten.listen_datei(args.quelle)

if args.ergeb_zeigen:
    # Bildschirmausgabe
    m_daten.listen_schirm()

# ----------------------------------------------------------------- Testlauf #
if args.testlauf:               # Spezialprüfung
    print('\n-- Spezialprüfung\n')
    m_daten.testausgabe()
    print()     # Leerzeile
    sys.exit(EXIT_OK)

# ------------------------------------------------------------- Datenfehler! #
if fehler:
    print('\n  *!*!*!* Fehler in den Daten !')
    if args.konf_datei:
        print('          daher keine Konfiguration geschrieben!')
    print()     # Leerzeile
    sys.exit(EXIT_DATA_ERROR)

# -------------------------------------------------- Konfiguration schreiben #
if not args.konf_datei:         # keine Dateien gewünscht
    print('\n-- Prüfung bestanden, keine Konfiguration geschrieben.\n')
    parser.print_usage()
    print()     # Leerzeile
    sys.exit(EXIT_OK)

# -------------------------------------------------------- Dateien schreiben #
if m_daten.schreib_konfig():
    print('\n  ** Während schreiben der Konfiguration Fehler gefunden! **\n')
    sys.exit(EXIT_DATA_INCONSISTENCE)

print('\n++ Prüfung bestanden, Konfiguration geschrieben.\n')
sys.exit(EXIT_OK)

# ------------------------------------------------------------- Ende Gelände #

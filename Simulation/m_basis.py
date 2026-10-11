"""
Verwalten von Basis-Daten, Informationen, Zuständen.
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# WICHTIG:
# Tunlichst kein anderes eigenes Modul importieren, um zirkuläre Importe zu vermeiden.
#
# Versionen
# 0.0 2019-02-21 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# 0.6 2020-02-08 wh Aufteilung wegen Problemen beim Import in m_basis und c_basis
# -------------------------------------------------------------------------- #

from m_ausgaben import MeldeTyp as MTyp, melde

# -------------------------------------------------- modulweite Definitionen #

# --- Variable
max_led_kanal = 0       # letzter LED-Kanal, zero-basiert
max_tast_kanal = 0      # letzter Tasten-Kanal, zero-basiert
blinkspannung = False   # True wenn die Blinkspannung geprüft wird

elemente = {}           # Schlüssel=Taste, Werte sind Weichen, Signale etc.
abschnitte = None       # Sammlung der Gleise
fahrstrassen = {}       # [TasteStartSignal,TasteZielSignal] = FahrstrObjekt

# -------------------------------------------------------------------------- #
def show_all_stati(melde_typ=MTyp.IMMER):
    """Ausgabe des Status von allen Elementen.
    :param melde_typ  MTyp  Ausgabe-Level der Status-Meldungen
    """
    melde(melde_typ, f'~~~~ Blinkspannung:{blinkspannung}')
    for v in elemente.values():
        v.show_status(melde_typ)

# ------------------------------------------------------------- Ende Gelände #

"""
Werkzeuge für die Excel-Analyse
"""
# -------------------------------------------------------------------------- #
# (c) 2019-2020 Walter Haschka
#
# Versionen
# 0.0 2019-02-01 wh Modul begonnen
# 0.5 2019-06-30 wh Phase 1 (PoC mit Basisfunktionalitäten) zur BAC2 fertig
# -------------------------------------------------------------------------- #

from openpyxl.utils.cell import get_column_letter, column_index_from_string

# ----------------------------------------------------------------- Methoden #
def wsGet(blatt, zeile, spalte):
    """Gibt den entsprechenden Wert zurück.
    :param blatt    Tabellenblatt
    :param zeile    Zeile
    :param spalte   Spalte
    :return         den Wert
    """
    return blatt.cell(row=zeile, column=spalte).value

# -------------------------------------------------------------------------- #
def wsSet(blatt, zeile, spalte, wert, stil=None):
    """Schreibt den entsprechenden Wert.
    :param blatt    Tabellenblatt
    :param zeile    Zeile
    :param spalte   Spalte
    :param wert     der neue Wert
    :param style    optionaler Stil für die Zelle
    :return     die Zelle
    """
    c = blatt.cell(row=zeile, column=spalte)
    c.value = wert
    if not stil is None:
        c.style = stil
    return c

# -------------------------------------------------------------------------- #
def col_ltr(index):
    """Umwandeln von numerischem Index in Spalten-Buchstabe.
    :param index    numerischer Index
    :param wert     Spalten-Buchstabe
    """
    return get_column_letter(index)

# -------------------------------------------------------------------------- #
def col_nmbr(index_str):
    """Umwandeln von Spalten-Buchstabe in numerischen Index.
    :param index_str    Index als Buchstabe
    :param wert         Nummer der Spalte
    """
    return column_index_from_string(index_str)

# -------------------------------------------------------------------------- #
def xls_range(spa1, zei1, spalten=0, zeilen=0):
    """Umwandeln eines gegebenen Zellbereichs in die Nomenklatur von Excel.
    :param spa1, zei1       erste Zelle des Bereichs
    :param spalten, zeilen  Anzahl der Spalten und Zeilen des Bereichs
    """
#     print(f'spa1={spa1} - zei1={zei1} : col2={spa1+spalten} - row2 = {zei1+zeilen}')
#     print(f'spa1={col_ltr(spa1)} {zei1} : col2={col_ltr(spa1+spalten)} {zei1+zeilen}')
    return f'{col_ltr(spa1)}{zei1}:{col_ltr(spa1+spalten)}{zei1+zeilen}'

# -------------------------------------------------------------------------- #
def merged_cell_last_col(blatt, zeile, spalte):
    """Liefert die letzte Spalte des Zellverbundes von welchem die angegebene
    Zelle ein Teil ist.
    :param blatt    Tabellenblatt
    :param zeile    Zeile
    :param spalte   Spalte
    """
    zelle = blatt.cell(zeile, spalte)
    for verbund in blatt.merged_cells.ranges:
        if zelle.coordinate in verbund:
#            print('bounds: {0}'.format(verbund.bounds) + f'\t last col={verbund.bounds[2]}')
            return verbund.bounds[2]

    raise ValueError(f'Zelle {col_ltr(spalte)}{zeile} nicht Teil eines Zellverbundes')

# ------------------------------------------------------------- Ende Gelände #

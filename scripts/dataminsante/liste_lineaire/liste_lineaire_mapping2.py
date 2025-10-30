# -*- coding: utf-8 -*-
# dataminsante/liste_lineaire/liste_lineaire_mapping.py

"""
Fonctions utilitaires pour la génération de fichiers Excel avec listes
déroulantes, validation et plages nommées.
"""
import pandas as pd
import re
from xlsxwriter.utility import xl_col_to_name

# ==============================
# Fonction pour noms Excel sûrs
# ==============================
def excel_safe_name(val):
    """
    Transforme une chaîne en nom valide pour Excel (plage nommée).
    
    Exemple : "Zone de santé" -> "Zone_de_sante"
    """
    if val is None or str(val).strip() == "":
        return ""
    s = str(val).strip()
    s = s.replace(" ", "_").replace("-", "_").replace("/", "_")
    s = re.sub(r"[^\w]", "", s)
    if not re.match(r"[A-Za-z_]", s[0]):
        s = "_" + s
    return s

# ==============================
# Fonction pour formules INDIRECT
# ==============================
def make_indirect_formula_for_col(source_col_index, top_data_row=2):
    """
    Génère une formule INDIRECT dynamique pour validation dépendante Excel.
    
    source_col_index : index de la colonne source
    top_data_row : ligne de début des données
    """
    col_letter = xl_col_to_name(source_col_index)
    cell_ref = f"${col_letter}{top_data_row}"
    return f"=INDIRECT(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({cell_ref},\" \",\"_\"),\"-\",\"_\"),\"/\",\"_\"))"

# ==============================
# Fonction pour écrire les catégories dans ref_data
# ==============================
def ecrire_ref_data(workbook, worksheet_ref, categories, start_col=0):
    """
    Écrit les catégories standardisées dans la feuille ref_data avec entêtes
    et crée des plages nommées pour chaque liste.
    
    Args:
        workbook : objet xlsxwriter.Workbook
        worksheet_ref : feuille de référence
        categories : dict {nom_liste: [valeurs]}
        start_col : colonne de départ (par défaut 0)
    
    Retour :
        prochaine colonne disponible (int)
    """
    col_idx = start_col
    for cat_name, values in categories.items():
        worksheet_ref.write(0, col_idx, cat_name)
        worksheet_ref.write_column(1, col_idx, values)
        col_letter = xl_col_to_name(col_idx)
        workbook.define_name(
            excel_safe_name(cat_name),
            f"ref_data!${col_letter}$2:${col_letter}${len(values)+1}"
        )
        col_idx += 1
    return col_idx

# ==============================
# Fonction pour ajouter une validation de liste à une colonne
# ==============================
def add_list_validation(worksheet, col_index, values, start_row=1, end_row=10000):
    """
    Ajoute une validation de type liste à une colonne Excel.

    Args:
        worksheet : xlsxwriter.worksheet
        col_index : int
        values : list ou str
        start_row : int
        end_row : int
    """
    source = values if isinstance(values, list) else f"={values}"
    worksheet.data_validation(
        start_row, col_index, end_row, col_index,
        {"validate": "list", "source": source}
    )

# ==============================
# Fonction pour écrire la hiérarchie Province / Zone / Aire
# ==============================
def ecrire_hierarchie_geo(
    workbook,
    worksheet_ref,
    df_geo,
    start_col=0,
    col_province_src="Province",
    col_zone_src="Zone_de_sante",
    col_aire_src="Aire_de_sante",
    col_province_dest=None,
    col_zone_dest=None,
    col_aire_dest=None
):
    """
    Crée la hiérarchie Province -> Zone -> Aire dans ref_data
    avec entêtes lisibles + suffixe '_list' et plages nommées uniques pour Excel.
    """
    if col_province_dest is None: col_province_dest = ["Province"]
    if col_zone_dest is None: col_zone_dest = ["Zone"]
    if col_aire_dest is None: col_aire_dest = ["Aire"]

    col_idx = start_col
    provinces = sorted(df_geo[col_province_src].dropna().unique())

    # --- Provinces ---
    for prov_dest in col_province_dest:
        entete = f"{prov_dest}_list"
        worksheet_ref.write(0, col_idx, entete)
        worksheet_ref.write_column(1, col_idx, provinces)
        workbook.define_name(
            excel_safe_name(prov_dest),  # plage = nom sûr
            f"ref_data!${xl_col_to_name(col_idx)}$2:${xl_col_to_name(col_idx)}${len(provinces)+1}"
        )
        col_idx += 1

    # --- Zones ---
    for prov in provinces:
        zones = sorted(df_geo.loc[df_geo[col_province_src] == prov, col_zone_src].dropna().unique())
        if zones:
            entete = f"{prov}_list"
            worksheet_ref.write(0, col_idx, entete)
            worksheet_ref.write_column(1, col_idx, zones)
            workbook.define_name(
                excel_safe_name(prov),
                f"ref_data!${xl_col_to_name(col_idx)}$2:${xl_col_to_name(col_idx)}${len(zones)+1}"
            )
            col_idx += 1

    # --- Aires ---
    for zone in sorted(df_geo[col_zone_src].dropna().unique()):
        aires = sorted(df_geo.loc[df_geo[col_zone_src] == zone, col_aire_src].dropna().unique())
        if aires:
            entete = f"{zone}_list"
            worksheet_ref.write(0, col_idx, entete)
            worksheet_ref.write_column(1, col_idx, aires)
            workbook.define_name(
                excel_safe_name(zone),
                f"ref_data!${xl_col_to_name(col_idx)}$2:${xl_col_to_name(col_idx)}${len(aires)+1}"
            )
            col_idx += 1

    return col_idx

# ==============================
# Fonction pour appliquer les validations dynamiques
# ==============================
def appliquer_validations_dynamiques(
    worksheet,
    col_notification,
    colonne_to_categorie,
    top_data_row=2,
    max_rows=10000
):
    for col_name, mapping in colonne_to_categorie.items():
        if col_name not in col_notification: continue
        col_index = col_notification.index(col_name)

        if isinstance(mapping, str) and mapping.startswith("INDIRECT_"):
            src_col = mapping.replace("INDIRECT_", "")
            if src_col in col_notification:
                src_idx = col_notification.index(src_col)
                dv_source = make_indirect_formula_for_col(src_idx, top_data_row=top_data_row)
            else: continue
        else:
            dv_source = f"={mapping}"

        worksheet.data_validation(
            top_data_row-1, col_index, max_rows, col_index,
            {"validate": "list", "source": dv_source}
        )

# ==============================
# Fonction pour générer le formulaire Excel complet
# ==============================
def generer_formulaire_geo(
    df_geo: pd.DataFrame,
    fichier_sortie: str,
    colonnes_formulaire: list[str],
    col_map: dict[str, str],
    col_province_src: str = "Province",
    col_zone_src: str = "Zone_de_sante",
    col_aire_src: str = "Aire_de_sante",
    col_province_dest: list[str] = None,
    col_zone_dest: list[str] = None,
    col_aire_dest: list[str] = None,
    max_rows: int = 10000
):
    with pd.ExcelWriter(fichier_sortie, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Formulaire")
        worksheet_ref = workbook.add_worksheet("ref_data")

        ecrire_hierarchie_geo(
            workbook,
            worksheet_ref,
            df_geo,
            start_col=0,
            col_province_src=col_province_src,
            col_zone_src=col_zone_src,
            col_aire_src=col_aire_src,
            col_province_dest=col_province_dest,
            col_zone_dest=col_zone_dest,
            col_aire_dest=col_aire_dest
        )

        # Écriture des entêtes dans Formulaire
        for col_index, col_name in enumerate(colonnes_formulaire):
            worksheet.write(0, col_index, col_name)

        # Application des validations dynamiques
        appliquer_validations_dynamiques(
            worksheet,
            col_notification=colonnes_formulaire,
            colonne_to_categorie=col_map,
            top_data_row=2,
            max_rows=max_rows
        )

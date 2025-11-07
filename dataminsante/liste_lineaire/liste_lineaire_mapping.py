# -*- coding: utf-8 -*-
# dataminsante/liste_lineaire/liste_lineaire_mapping.py

"""
Fonctions utilitaires pour la génération de fichiers Excel avec listes
déroulantes, validation et plages nommées.
"""
import pandas as pd
import re
from xlsxwriter.utility import xl_col_to_name
from collections import defaultdict
import logging

# Config basique du logging si pas encore défini
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ==============================
# Fonction utilitaires
# ==============================

def excel_safe_name(val, add_list=True):
    """
    Transforme une chaîne en nom valide pour Excel (plage nommée).
    """
    if val is None or str(val).strip() == "":
        return "_empty"
    s = str(val).strip().replace(" ", "_").replace("-", "_").replace("/", "_")
    s = re.sub(r"[^\w]", "", s)
    if not re.match(r"[A-Za-z_]", s[0]):
        s = "_" + s
    if add_list:
        s += "_list"
    return s

def make_indirect_formula_for_col(source_col_index, top_data_row=2, excel_lang="en", add_list=True):
    """
    Génère une formule INDIRECT dynamique pour validation dépendante Excel,
    en utilisant excel_safe_name pour sécuriser le nom de plage.
    
    Args:
        source_col_index : index de la colonne source (0-based)
        top_data_row : ligne du premier enregistrement (par défaut 2)
        excel_lang : 'fr' ou 'en' (pour Excel FR/EN)
        add_list : ajouter le suffixe '_list' automatiquement (bool)
        
    Retour :
        str : formule Excel prête à coller dans data_validation
    """
    col_letter = xl_col_to_name(source_col_index)
    cell_ref = f"${col_letter}${top_data_row}"

    # On applique la substitution côté Excel pour compatibilité
    if excel_lang.lower() == "fr":
        formula = f"SUBSTITUE(SUBSTITUE(SUBSTITUE({cell_ref};\" \";\"_\");\"-\";\"_\");\"/\";\"_\")"
    else:
        formula = f"SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({cell_ref},\" \",\"_\"),\"-\",\"_\"),\"/\",\"_\")"
    
    # Ajout du suffixe _list si demandé
    if add_list:
        formula += '&"_list"'
    
    # On encapsule dans INDIRECT
    return f"=INDIRECT({formula})"


# Fonction pour écrire les catégories dans ref_data
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

# Fonction pour ajouter une validation de liste à une colonne
def add_list_validation(worksheet, col_index, values, start_row=1, end_row=10000):
    """
    Ajoute une validation de type liste à une colonne Excel.
    
    worksheet : objet xlsxwriter.worksheet
    col_index : index de la colonne à valider
    values : liste de valeurs ou nom de plage Excel (str)
    start_row : ligne de départ (défaut 1)
    end_row : ligne de fin (défaut 10000)
    """
    source = values if isinstance(values, list) else f"={values}"
    worksheet.data_validation(
        start_row, col_index, end_row, col_index,
        {"validate": "list", "source": source}
    )



# faire le mapping avec merge   
def merge_dicts_keep_all(*dicts):
    merged = defaultdict(list)
    for d in dicts:
        for k, v in d.items():
            if isinstance(v, list):
                merged[k].extend(v)
            else:
                merged[k].append(v)
    # Supprimer les doublons éventuels
    return {k: sorted(set(v)) if len(v) > 1 else v[0] for k, v in merged.items()}

# Fonction pour écrire la hiérarchie Province / Zone / Aire
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

def generer_formulaire_geo(
    df_geo: pd.DataFrame,
    fichier_sortie: str,
    colonnes_formulaire: list[str] = None,
    col_map: dict[str, str] = None,
    col_province_src: str = "Province",
    col_zone_src: str = "Zone_de_sante",
    col_aire_src: str = "Aire_de_sante",
    col_province_dest: str = None,
    col_zone_dest: str = None,
    col_aire_dest: str = None,
    max_lignes=None,
    excel_lang: str = "en"  # 'fr' pour français, 'en' pour anglais
):
    """
    Crée un fichier Excel hiérarchique avec listes déroulantes dépendantes.
    - excel_lang: 'fr' ou 'en' pour Excel FR ou EN
    """

    df = df_geo.copy()
    
    # Vérifier les colonnes
    for col in [col_province_src, col_zone_src, col_aire_src]:
        if col not in df.columns:
            raise ValueError(f"La colonne '{col}' n'existe pas dans le DataFrame.")

    # Noms normalisés
    col_province_dest = col_province_dest or "Province_nom"
    col_zone_dest = col_zone_dest or "Zone_nom"
    col_aire_dest = col_aire_dest or "Aire_nom"

    # Normalisation pour les plages Excel
    df[col_province_dest] = df[col_province_src].apply(lambda x: excel_safe_name(x, add_list=True))
    df[col_zone_dest] = df[col_zone_src].apply(lambda x: excel_safe_name(x, add_list=True))
    df[col_aire_dest] = df[col_aire_src].apply(lambda x: excel_safe_name(x, add_list=True))

    max_rows = len(df) if max_lignes is None else max_lignes

    with pd.ExcelWriter(fichier_sortie, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Formulaire")
        worksheet_ref = workbook.add_worksheet("ref_data")

        # --- Écriture ref_data ---
        col_idx = 0
        provinces = sorted(df[col_province_src].dropna().unique())
        worksheet_ref.write(0, col_idx, "Provinces_list")
        worksheet_ref.write_column(1, col_idx, provinces)
        workbook.define_name("Provinces_list", f"ref_data!$A$2:$A${len(provinces)+1}")
        col_idx += 1

        zone_seen = set()
        aire_seen = set()

        # Zones par province
        for prov in provinces:
            zones = sorted(df.loc[df[col_province_src] == prov, col_zone_src].dropna().unique())
            if zones:
                header_name = excel_safe_name(prov, add_list=True)
                worksheet_ref.write(0, col_idx, header_name)
                worksheet_ref.write_column(1, col_idx, zones)
                col_letter = xl_col_to_name(col_idx)
                workbook.define_name(header_name, f"ref_data!${col_letter}$2:${col_letter}${len(zones)+1}")
                col_idx += 1
                zone_seen.update(zones)

        # Aires par zone
        for zone in sorted(zone_seen):
            aires = sorted(df.loc[df[col_zone_src] == zone, col_aire_src].dropna().unique())
            if aires:
                header_name = excel_safe_name(zone, add_list=True)
                worksheet_ref.write(0, col_idx, header_name)
                worksheet_ref.write_column(1, col_idx, aires)
                col_letter = xl_col_to_name(col_idx)
                workbook.define_name(header_name, f"ref_data!${col_letter}$2:${col_letter}${len(aires)+1}")
                col_idx += 1
                aire_seen.update(aires)

        # --- Formulaire ---
        if colonnes_formulaire is None:
            colonnes_formulaire = [col_province_src, col_zone_src, col_aire_src]
        for idx, col_name in enumerate(colonnes_formulaire):
            worksheet.write(0, idx, col_name)

        # --- Map par défaut ---
        if col_map is None:
            col_map = {
                col_province_src: "Provinces_list",
                col_zone_src: "INDIRECT_Province",
                col_aire_src: "INDIRECT_Zone_de_sante"
            }

        # --- Formules INDIRECT selon langue ---
        def formule_indirect(cell_ref):
            if excel_lang.lower() == "fr":
                return f'=INDIRECT(SUBSTITUE(SUBSTITUE(SUBSTITUE({cell_ref};" ";"_");"-";"_");"/";"_")&"_list")'
            else:
                return f'=INDIRECT(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({cell_ref}," ","_"),"-","_"),"/","_")&"_list")'

        # --- Appliquer les validations ---
        for col_name, mapping in col_map.items():
            if col_name not in colonnes_formulaire: 
                continue
            col_index = colonnes_formulaire.index(col_name)
            if isinstance(mapping, str) and mapping.startswith("INDIRECT_"):
                src_col_name = mapping.replace("INDIRECT_", "")
                if src_col_name in colonnes_formulaire:
                    src_idx = colonnes_formulaire.index(src_col_name)
                    cell_ref = xl_col_to_name(src_idx) + "2"
                    dv_source = formule_indirect(cell_ref)
                else:
                    continue
            else:
                dv_source = f"={mapping}"

            worksheet.data_validation(1, col_index, max_rows, col_index,
                                      {"validate": "list", "source": dv_source})
            
def generate_excel_standard(
    colonnes: list,
    categories: dict,
    col_map: dict,
    df_geo=None,
    colonnes_date=None,
    colonnes_heure=None,
    colonnes_numerique=None,
    indirect_map=None,
    fichier_sortie: str = "output.xlsx",
    excel_lang: str = "fr",
    max_rows: int = 5000
):
    from pathlib import Path
    import xlsxwriter
    import logging
    from datetime import datetime, time
    from xlsxwriter.utility import xl_col_to_name

    # --- mapping INDIRECT par défaut si rien passé ---
    if indirect_map is None:
        indirect_map = {
            "Zone de santé de notification": "Province de notification",
            "Aire de santé de notification": "Zone de santé de notification",
            "Zone de santé de provenance": "Province de provenance",
        }

    # Défaut colonnes
    colonnes_date = colonnes_date or []
    colonnes_heure = colonnes_heure or []
    colonnes_numerique = colonnes_numerique or []

    # Préparation fichier
    Path(fichier_sortie).parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(fichier_sortie)
    ws_data = workbook.add_worksheet("data")
    ws_ref = workbook.add_worksheet("ref_data")

    # --- ref_data ---
    col_idx_ref = ecrire_ref_data(workbook, ws_ref, categories, start_col=0)

    # --- Hiérarchie Province → Zone → Aire ---
    if df_geo is not None:
        provinces = sorted(df_geo["Province"].dropna().unique())
        ws_ref.write(0, col_idx_ref, "Provinces_list")
        ws_ref.write_column(1, col_idx_ref, provinces)
        workbook.define_name(
            "Provinces_list",
            f"ref_data!${xl_col_to_name(col_idx_ref)}$2:${xl_col_to_name(col_idx_ref)}${len(provinces)+1}"
        )
        col_idx_ref += 1

        zone_seen = set()
        for prov in provinces:
            zones = sorted(df_geo.loc[df_geo["Province"] == prov, "Zone_de_sante"].dropna().unique())
            if zones:
                safe_prov = excel_safe_name(prov, add_list=True)
                ws_ref.write(0, col_idx_ref, safe_prov)
                ws_ref.write_column(1, col_idx_ref, zones)
                workbook.define_name(
                    safe_prov,
                    f"ref_data!${xl_col_to_name(col_idx_ref)}$2:${xl_col_to_name(col_idx_ref)}${len(zones)+1}"
                )
                col_idx_ref += 1
                zone_seen.update(zones)

        for zone in sorted(zone_seen):
            aires = sorted(df_geo.loc[df_geo["Zone_de_sante"] == zone, "Aire_de_sante"].dropna().unique())
            if aires:
                safe_zone = excel_safe_name(zone, add_list=True)
                ws_ref.write(0, col_idx_ref, safe_zone)
                ws_ref.write_column(1, col_idx_ref, aires)
                workbook.define_name(
                    safe_zone,
                    f"ref_data!${xl_col_to_name(col_idx_ref)}$2:${xl_col_to_name(col_idx_ref)}${len(aires)+1}"
                )
                col_idx_ref += 1

    # --- Formats ---
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
    date_fmt = workbook.add_format({"num_format": "dd/mm/yyyy"})
    time_fmt = workbook.add_format({"num_format": "hh:mm"})
    min_date, max_date = datetime(1900, 1, 1), datetime(2100, 12, 31)
    min_time, max_time = time(0,0,0), time(23,59,59)

    # --- Validation colonnes ---
    for idx, col in enumerate(colonnes):
        ws_data.write(0, idx, col, header_fmt)

        # --- Heures ---
        if col in colonnes_heure:
            ws_data.set_column(idx, idx, 12, time_fmt)
            ws_data.data_validation(1, idx, max_rows, idx, {
                "validate":"time","criteria":"between",
                "minimum":min_time,"maximum":max_time,
                "input_message":f"Veuillez entrer l'heure au format HH:MM (ex: 19:18)"
            })
            
        # --- Dates ---
        elif col in colonnes_date:
            ws_data.set_column(idx, idx, 15, date_fmt)
            ws_data.data_validation(1, idx, max_rows, idx, {
                "validate":"date","criteria":"between",
                "minimum":min_date,"maximum":max_date,
                "input_message":f"Veuillez entrer une date valide (jj/mm/aaaa) ex: 08/09/2025"
            })
        # --- Nombres (ex: Age) ---
        elif col in colonnes_numerique:
            ws_data.data_validation(1, idx, max_rows, idx, {
                "validate":"whole","criteria":"between",
                "minimum":0,"maximum":150,
                "input_message":f"Entrez un âge entier entre 0 et 150 (ex: 25)"
            })
            
        # --- Listes / catégories ---
        elif col in col_map:
            named_range = col_map[col]
            if named_range.startswith("INDIRECT"):
                if col in indirect_map:
                    source_col_name = indirect_map[col]
                    source_col = colonnes.index(source_col_name)
                    dv_source = make_indirect_formula_for_col(
                        source_col, excel_lang=excel_lang
                    )
                else:
                    raise ValueError(f"Pas de mapping INDIRECT défini pour {col}")
            else:
                dv_source = f"={excel_safe_name(named_range)}"

            ws_data.data_validation(1, idx, max_rows, idx, {
                "validate":"list","source":dv_source,
                "input_message":f"Sélectionnez dans la liste ({col})"
            })

    # --- Finalisation ---
    ws_data.freeze_panes(1,0)
    ws_data.autofilter(0,0,0,len(colonnes)-1)
    workbook.close()
    logging.warning(f"✅ Fichier généré : {fichier_sortie}")


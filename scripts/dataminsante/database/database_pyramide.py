# -*- coding: utf-8 -*-

# dataminsante/database_pyramide.py

import pandas as pd
from pathlib import Path
import logging
from dataminsante.colonne_valeur.colonne_nettoyage import * 
from dataminsante.colonne_valeur.valeurs_nettoyage import *


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# base_dir pointe sur le dossier data (pour fichiers Excel)
base_dir = Path(__file__).resolve().parents[2] / "data"

# Chemins des fichiers
path_province = base_dir / "rdc_provinces.xlsx"
path_antenne = base_dir / "rdc_antennes.xlsx"
path_zone_sante = base_dir / "rdc_zones_sante.xlsx"
path_aire_sante = base_dir / "rdc_aires_sante.xlsx"
path_structure_sanitaire = base_dir / "rdc_structures_sanitaires.xlsx"
path_database_pyramide = base_dir / "rdc_database_pyramide_code.xlsx"

# Codes provinces à deux lettres
code_provinces_deux_lettres = {
    "bu": "Bas Uele",
    "eq": "Equateur",
    "hk": "Haut Katanga",
    "hl": "Haut Lomami",
    "hu": "Haut Uele",
    "it": "Ituri",
    "kr": "Kasai Central",
    "ks": "Kasai",
    "kn": "Kinshasa",
    "kc": "Kongo Central",
    "ke": "Kasai Oriental",
    "kg": "Kwango",
    "kl": "Kwilu",
    "lm": "Lomami",
    "ll": "Lualaba",
    "md": "Maindombe",
    "mn": "Maniema",
    "mg": "Mongala",
    "nk": "Nord Kivu",
    "nu": "Nord Ubangi",
    "sn": "Sankuru",
    "sk": "Sud Kivu",
    "su": "Sud Ubangi",
    "tn": "Tanganyika",
    "tu": "Tshuapa",
    "tp": "Tshopo"
}
# Codes provinces à trois lettres
code_provinces_trois_lettres = {
    "BUE": "Bas Uele",
    "EQU": "Equateur",
    "HKA": "Haut Katanga",
    "HLO": "Haut Lomami",
    "HUE": "Haut Uele",
    "ITU": "Ituri",
    "KAC": "Kasai Central",
    "KAS": "Kasai",
    "KIN": "Kinshasa",
    "KOC": "Kongo Central",
    "KOR": "Kasai Oriental",
    "KWA": "Kwango",
    "KWI": "Kwilu",
    "LOM": "Lomami",
    "LUA": "Lualaba",
    "MAI": "Maindombe",
    "MAN": "Maniema",
    "MON": "Mongala",
    "NKV": "Nord Kivu",
    "NUB": "Nord Ubangi",
    "SAN": "Sankuru",
    "SKV": "Sud Kivu",
    "SUB": "Sud Ubangi",
    "TAN": "Tanganyika",
    "TSH": "Tshuapa",
    "TSO": "Tshopo"
}
# Trouver les codes provinces à partir des deux et trois lettres
def trouver_province(provenance, mapping: dict, longueur_code: int = 2) -> str:
    """
    Extrait le code depuis la valeur de provenance et retourne le nom de la province correspondante.

    Args:
        provenance (str): La valeur de la colonne (ex: 'eq_XXX_LL').
        mapping (dict): Dictionnaire de correspondance code -> nom de province.
        longueur_code (int): Nombre de caractères pour le code (par défaut 2).

    Returns:
        str: Nom de la province ou None si non trouvée ou entrée vide.
    """
    if pd.isna(provenance):
        return None

    provenance_str = str(provenance).strip().lower()
    code = provenance_str[:longueur_code]

    province = mapping.get(code)
    logging.info(f"🔍 Code: {code} → Province: {province}")
    return province

# Trouver une province standard
def trouver_province_standard(provenance: str, mapping: dict, valeur_avant="DPS_", valeur_apres="_SE") -> str:
    """
    Extrait le code province depuis la valeur de provenance
    en utilisant trouve_caractere et retourne le nom de la province correspondante.

    Args:
        provenance (str): La valeur de la colonne "Provenance"
                          (ex: 'LLCholera_DPS_KIN_SE33_20250819').
        mapping (dict): Dictionnaire de correspondance code -> nom de province.
                        (ex: {"KIN": "Kinshasa", "KAT": "Haut-Katanga"})
        valeur_avant (str): Motif avant le code (par défaut 'DPS_').
        valeur_apres (str): Motif après le code (par défaut '_SE').

    Returns:
        str: Nom de la province ou None si non trouvée.
    """
    if not provenance:
        return None

    code = trouve_caractere(provenance, valeur_avant, valeur_apres)
    return mapping.get(code, None)



# ---------------------------------------------
# Extraction du type et du nom de structure
# ---------------------------------------------
def extraire_structure_info(texte):
    types_composes = {"Ant Pev"}  # Ajouter d'autres types composés si besoin
    if isinstance(texte, str):
        texte = texte.strip().title()
        for type_compose in types_composes:
            if texte.startswith(type_compose):
                reste = texte[len(type_compose):].strip()
                return type_compose, reste
        parts = texte.split(maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return parts[0], ""
    return "", ""

def extraire_type_et_nom_structure(df, cols):
    if isinstance(cols, str):
        cols = [cols]

    for col in cols:
        if col in df.columns:
            result = df[col].apply(extraire_structure_info)
            df[f'Type_structure_{col}'] = result.apply(lambda x: x[0])
            df[f'Nom_structure_{col}'] = result.apply(lambda x: x[1])

    return df


# ---------------------------------------------
# Nettoyage des entités administratives
# ---------------------------------------------

def lire_excel_secure(path):
    try:
        return pd.read_excel(path).copy()
    except FileNotFoundError:
        logging.warning(f"Fichier non trouvé : {path}")
        return pd.DataFrame()

def clean_provinces():
    logging.info("Chargement et nettoyage des provinces...")
    rdc_provinces = lire_excel_secure(path_province)
    if rdc_provinces.empty:
        logging.warning("Le fichier provinces est vide ou introuvable.")
        return rdc_provinces
    rdc_provinces = clean_all_column_names(rdc_provinces)
    return rdc_provinces

def clean_antennes():
    logging.info("Chargement et nettoyage des antennes...")
    rdc_antennes = lire_excel_secure(path_antenne)
    if rdc_antennes.empty:
        logging.warning("Le fichier antennes est vide ou introuvable.")
        return rdc_antennes
    rdc_antennes = clean_all_column_names(rdc_antennes)
    rdc_antennes = replace_specific_values(rdc_antennes)
    rdc_antennes = clean_first_letter_values(rdc_antennes, ['Province', 'Antenne'])

    rdc_provinces = clean_provinces()
    rdc_antennes = pd.merge(rdc_provinces, rdc_antennes, how='left', on='Province')

    colonnes_base = ['Pays', 'Province', 'Code_Province', 'Antenne']
    return rdc_antennes[colonnes_base]

def clean_zones_de_sante():
    logging.info("Chargement et nettoyage des zones de santé...")
    zones = lire_excel_secure(path_zone_sante)
    if zones.empty:
        logging.warning("Le fichier zones de santé est vide ou introuvable.")
        return zones
    zones = clean_all_column_names(zones)
    zones = replace_specific_values(zones)
    zones = clean_first_letter_values(zones, ['Province', 'Sous_province', 'Zone_de_sante'])
    zones.rename(columns={'Sous_province': 'Antenne'}, inplace=True)

    rdc_provinces = clean_provinces()
    merged = pd.merge(rdc_provinces, zones, how='left', on='Province')

    colonnes_base = ['Pays', 'Province', 'Code_Province', 'Antenne', 'Zone_de_sante']
    autres = [col for col in merged.columns if col not in colonnes_base]
    return merged[colonnes_base + autres]

def clean_aires_de_sante():
    logging.info("Chargement et nettoyage des aires de santé...")
    df = lire_excel_secure(path_aire_sante)
    if df.empty:
        logging.warning("Le fichier aires de santé est vide ou introuvable.")
        return df
    df = clean_all_column_names(df)
    df = replace_specific_values(df)
    df = clean_first_letter_values(df, ['Province', 'Antenne', 'Zone_de_sante'])

    rdc_provinces = clean_provinces()
    df = pd.merge(df, rdc_provinces[['Province', 'Code_Province']], on='Province', how='left')

    df[['Type_de_structure', 'Nom_de_structure']] = df['Structure_sanitaire'].apply(extraire_structure_info).apply(pd.Series)

    colonnes_base = ['ID_StructureSanitaire', 'Pays', 'Province', 'Code_Province', 'Antenne', 'Zone_de_sante',
                     'Structure_sanitaire', 'Type_de_structure', 'Nom_de_structure']
    autres = [col for col in df.columns if col not in colonnes_base]
    return df[colonnes_base + autres]

def clean_structures_sanitaires():
    logging.info("Chargement et nettoyage des structures sanitaires...")
    df = lire_excel_secure(path_structure_sanitaire)
    if df.empty:
        logging.warning("Le fichier structures sanitaires est vide ou introuvable.")
        return df
    df = clean_all_column_names(df)
    df = replace_specific_values(df)
    df = clean_first_letter_values(df, ['Province', 'Antenne', 'Zone_de_sante'])

    rdc_provinces = clean_provinces()
    df = pd.merge(df, rdc_provinces[['Province', 'Code_Province']], on='Province', how='left')

    df[['Type_de_structure', 'Nom_de_structure']] = df['Structure_sanitaire'].apply(extraire_structure_info).apply(pd.Series)

    colonnes_base = ['ID_StructureSanitaire', 'Pays', 'Province', 'Code_Province', 'Antenne', 'Zone_de_sante',
                     'Structure_sanitaire', 'Type_de_structure', 'Nom_de_structure']
    autres = [col for col in df.columns if col not in colonnes_base]
    return df[colonnes_base + autres]

def clean_database_pyramide():
    logging.info("Chargement et nettoyage du fichier de décentralisation...")
    
    df = lire_excel_secure(path_database_pyramide)
    if df.empty:
        logging.warning("Le fichier de décentralisation est vide ou introuvable.")
        return df

    # Nettoyage des majuscules en début (Province, Zone...)
    df = clean_first_letter_values(df, ['Province', 'Zone_de_sante','Aire_de_sante'])

    # Tri et structuration : colonnes de base
    colonnes_base = [
        'Code_Pays', 'Province', 'Code_Province',
        'Zone_de_sante', 'Code_zone_de_sante','Aire_de_sante'
    ]

    return df[colonnes_base]


# ---------------------------------------------
# Fonction générique
# ---------------------------------------------
def charger_et_nettoyer_database_pyramide(path, colonnes_a_normaliser):
    logging.info(f"Chargement et nettoyage du fichier : {path}")
    df = lire_excel_secure(path)
    if df.empty:
        logging.warning(f"Le fichier {path} est vide ou introuvable.")
        return df
    df = clean_all_column_names(df)
    df = replace_specific_values(df)
    df = clean_first_letter_values(df, colonnes_a_normaliser)
    return df

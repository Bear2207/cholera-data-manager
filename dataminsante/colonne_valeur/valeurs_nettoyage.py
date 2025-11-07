# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/valeurs_nettoyage.py

# Notice : Des fonctions rapides pour le nettoyage des valeurs des colonnes du df

import os
import re
import logging
import unicodedata
from pathlib import Path
from typing import List, Union

import pandas as pd
from dateutil import parser


# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fichier de remplacement des valeurs
base_dir = Path(__file__).resolve().parents[2]
mapping_file_path = base_dir / "data" / "Replace_values.xlsx"

# Nettoyage valeurs vides
def nettoyer_valeurs_vides(df: pd.DataFrame, log: bool = False) -> pd.DataFrame:
    """
    Nettoyer les valeurs équivalentes à NA selon le type de colonne.

    Cette fonction remplace les valeurs textuelles équivalentes à "NaN", "<na>", "None", etc.
    puis remplit les cellules vides :
        - Par '' pour les colonnes texte
        - Par pd.NA pour les colonnes numériques

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame à nettoyer.
    log : bool, optionnel
        Si True, enregistre les actions dans les logs.

    Retour
    ------
    pd.DataFrame
        DataFrame nettoyé avec valeurs cohérentes selon le type de colonne.

    Exemple
    -------
    >>> df = pd.DataFrame({
    ...     'Nom': ['Alice', '<na>', None],
    ...     'Age': [25, None, 130],
    ...     'Score': ['NaN', '12', 'None']
    ... })
    >>> df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
    >>> df = nettoyer_valeurs_vides(df, log=True)
    """
    # Initialisation du logger si demandé
    if log:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 1️⃣ Remplacer les valeurs équivalentes à NA
    valeurs_equivalentes = ['<na>', 'NaN', 'nan', 'None', 'Nan']
    df = df.replace(valeurs_equivalentes, pd.NA, regex=False)
    if log:
        logging.info("Remplacement des valeurs équivalentes à NA effectué.")

    # 2️⃣ Colonnes texte
    cols_text = df.select_dtypes(include=['object', 'string']).columns
    df[cols_text] = df[cols_text].fillna('')
    if log and len(cols_text) > 0:
        logging.info(f"Colonnes texte nettoyées : {list(cols_text)}")

    # 3️⃣ Colonnes numériques
    cols_num = df.select_dtypes(include=['Int64', 'float64']).columns
    df[cols_num] = df[cols_num].fillna(pd.NA)
    if log and len(cols_num) > 0:
        logging.info(f"Colonnes numériques nettoyées : {list(cols_num)}")

    if log:
        logging.info("Nettoyage des valeurs vides terminé.")

    return df

# Nettoyage valeur
def normaliser_values(df, cols, case_option="title", remove_accents=False):
    """
    Normalise une colonne de texte Pandas Series :

    1. Supprime les espaces en début/fin
    2. Remplace '-' et '_' par un espace
    3. Réduit les espaces multiples à un seul
    4. Capitalisation selon style :
       - "upper" : tout en majuscule
       - "lower" : tout en minuscule
       - "capitalize" : première lettre du texte en majuscule
       - "title" : première lettre de chaque mot en majuscule (par défaut)
    5. Supprime les accents si remove_accents=True
    """
    def retirer_accents(text):
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
    
    def nettoyer(val):
        if not isinstance(val, str):
            return val
        val = val.strip()
        val = re.sub(r"[-_]", " ", val)
        val = re.sub(r"\s+", " ", val)
        if remove_accents:
            val = retirer_accents(val)
        if case_option == "upper":
            val = val.upper()
        elif case_option == "lower":
            val = val.lower()
        elif case_option == "capitalize":
            val = val.capitalize()
        else:  # title
            val = val.title()
        return val

    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(nettoyer)
            logging.info(f"Colonne '{col}' normalisée.")
        else:
            logging.warning(f"Colonne '{col}' non trouvée dans le DataFrame.")
    
    return df

# ----------------------------------------------------------
# --- Fonction utilitaire pour gérer les colonnes cibles ---
# ----------------------------------------------------------
def get_target_columns(df, cols, allow_all_if_none=True):
    """
    Résout les colonnes cibles dans un DataFrame :
    - Si None : toutes les colonnes ou liste vide (selon allow_all_if_none)
    - Si str : liste avec un seul élément
    - Si list : seulement celles présentes dans df.columns
    """

    if cols is None:
        if allow_all_if_none:
            return df.columns.tolist()
        else:
            return []

    if isinstance(cols, str):
        if cols in df.columns:
            return [cols]
        else:
            logger.warning(f"❗ Colonne '{cols}' non trouvée dans le DataFrame.")
            return []

    # C'est une liste
    result = [col for col in cols if col in df.columns]
    missing = set(cols) - set(result)
    if missing:
        logger.warning(f"❗ Colonnes non trouvées : {list(missing)}")

    return result

def strip_accents(text):
    """
    Supprime les accents d'une chaîne.
    Si text est None, pd.NA ou non str, le retourne tel quel.
    """
    if text is None or pd.isna(text):
        return text
    if not isinstance(text, str):
        return text

    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c))

# Valeurs NA à considérer comme manquantes
na_values = {
        '', ' ', '-','Inconnu', 'Non renseigné', 'N/A', 'NaN', 'null', 'None', 'nan',
        'non renseigné', 'aucune', 'aucun', 'aucune information', 'aucune donnée',
        'aucune donnée renseignée', 'INCONNU', 'inconnu', 'inconue', 'non', 'Non','None',
        'N/A', 'n/a', 'na', 'nan', 'null', 'aucune information', 'aucune donnée',
        '<na>', 'nan', 'NAN', 'Aucun', 'aucun', 'aucune','<NA>'
    }


# ----------------------------------------------------------
# Fonction générique
# ----------------------------------------------------------

# --- Remplacer des valeurs selon un mapping Excel ---
def replace_specific_values(df, mapping_file=mapping_file_path):
    if not mapping_file.exists():
        raise FileNotFoundError(f"Fichier de mapping introuvable : {mapping_file}")

    mapping_df = pd.read_excel(mapping_file, dtype=str).dropna(how='any')
    replace_dict = dict(zip(mapping_df.iloc[:, 0].str.strip(), mapping_df.iloc[:, 1].str.strip()))

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].replace(replace_dict)

    return df

# --- vérifier les regex dans le mapping Excel pour une variable spécifique ---
def verifier_regex_mapping(
    fichier_mapping: Union[str, Path] = mapping_file_path, 
    variable: Union[str, List[str]] = ""
    ):
    df_map = pd.read_excel(fichier_mapping, dtype=str).dropna(how="any")
    df_map.columns = [col.strip().lower() for col in df_map.columns]

    df_map = df_map[df_map["variable"].str.lower() == variable.lower()]
    valides, invalides = [], []

    for _, row in df_map.iterrows():
        pattern = str(row["original"]).strip()
        try:
            re.compile(pattern)
            valides.append(pattern)
        except re.error as e:
            invalides.append((pattern, str(e)))

    logger.info(f"✔️ Regex valides ({len(valides)}):")
    for p in valides:
        logger.info(f"  - {p}")

    if invalides:
        logger.warning(f"❌ Regex invalides ({len(invalides)}):")
        for p, err in invalides:
            logger.warning(f"  - {p} → {err}")
    else:
        logger.info("✅ Toutes les regex sont valides.")
        
# --- Remplacer des valeurs selon un mapping Excel pour des colonnes spécifiques avec critères ---
def replace_specific_values_critere(
    df: pd.DataFrame,
    mapping_file: Union[str, Path]= mapping_file_path,
    critere: dict = {},
    regex_mode: bool = False,
    clean_before: bool = True,
    strip_lower: bool = True,
    verifier_regex_avant: bool = False,
    log_clean_preview: bool = False
) -> pd.DataFrame:
    """
    Remplace les valeurs dans un DataFrame en utilisant un fichier Excel de mapping
    contenant les colonnes 'Original', 'Renamed' et 'Variable'. Permet le mapping direct ou regex,
    avec nettoyage et prétraitement.

    Args:
        df: Le DataFrame à traiter
        mapping_file: Chemin du fichier Excel
        critere: Dictionnaire {colonne_df: nom_variable_mapping}
        regex_mode: Si True, applique les regex (fullmatch)
        clean_before: Nettoie les valeurs (strip, etc.) avant correspondance
        strip_lower: Convertit en minuscules pour les correspondances exactes
        verifier_regex_avant: Vérifie les regex du mapping (détection d’erreurs)
        log_clean_preview: Affiche un aperçu des valeurs brutes avant remplacement

    Returns:
        DataFrame nettoyé avec les valeurs remplacées
    """

    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"❌ Fichier de mapping introuvable : {mapping_file}")

    # Lecture du mapping Excel
    mapping_df = pd.read_excel(mapping_file, dtype=str).dropna(how="any")
    mapping_df.columns = [col.strip().lower() for col in mapping_df.columns]

    required_cols = {"original", "renamed", "variable"}
    if not required_cols.issubset(set(mapping_df.columns)):
        raise ValueError(f"❌ Fichier mapping invalide. Colonnes requises : {required_cols}")

    # Vérification des regex avant application
    if regex_mode and verifier_regex_avant:
        for variable_mapping in critere.values():
            verifier_regex_mapping(mapping_file, variable_mapping)

    df_clean = df.copy()

    for col_df, variable_mapping in critere.items():
        if col_df not in df_clean.columns:
            logger.warning(f"[Nettoyage ignoré] Colonne '{col_df}' absente du DataFrame.")
            continue

        sous_mapping = mapping_df[
            mapping_df["variable"].str.lower() == variable_mapping.lower()
        ]
        if sous_mapping.empty:
            logger.warning(f"[Nettoyage ignoré] Aucun mapping trouvé pour la variable '{variable_mapping}'.")
            continue

        logger.info(f"[Nettoyage] Colonne '{col_df}' → variable '{variable_mapping}' ({len(sous_mapping)} lignes)")

        # Prétraitement des valeurs
        if clean_before:
            df_clean[col_df] = df_clean[col_df].astype(str).str.strip()
            if strip_lower:
                df_clean[col_df] = df_clean[col_df].str.lower()
            if log_clean_preview:
                apercu = df_clean[col_df].dropna().unique()[:5]
                logger.info(f"[Prétraitement] Exemples valeurs de '{col_df}': {apercu}")

        # --- Mapping exact
        if not regex_mode:
            mapping_keys = sous_mapping["original"].astype(str).str.strip()
            if strip_lower:
                mapping_keys = mapping_keys.str.lower()
            mapping_values = sous_mapping["renamed"].astype(str).str.strip()

            replace_dict = dict(zip(mapping_keys, mapping_values))
            df_clean[col_df] = df_clean[col_df].replace(replace_dict)
            logger.info(f"[Mapping exact] {len(replace_dict)} correspondances appliquées à '{col_df}'")

        # --- Mapping regex
        else:
            patterns = []
            erreurs_regex = 0

            for _, row in sous_mapping.iterrows():
                original = str(row["original"]).strip()
                renamed = str(row["renamed"]).strip()
                try:
                    pattern = re.compile(original, re.IGNORECASE)
                    patterns.append((pattern, renamed))
                except re.error as e:
                    erreurs_regex += 1
                    logger.warning(f"[Regex ignorée] '{original}' → {e}")

            def apply_regex(val):
                val_str = str(val).strip()
                for pattern, remplacement in patterns:
                    if pattern.fullmatch(val_str):
                        return remplacement
                return val

            df_clean[col_df] = df_clean[col_df].apply(apply_regex)
            logger.info(f"[Mapping regex] {len(patterns)} patterns valides appliqués à '{col_df}'")
            if erreurs_regex:
                logger.warning(f"[Mapping regex] {erreurs_regex} regex invalides ignorées pour '{variable_mapping}'")

    return df_clean

# --- Nettoyer : première lettre de chaque mot en majuscule (ex: "jean pierre" → "Jean Pierre") ---
def clean_first_letter_values(df, cols=None):
    cols = get_target_columns(df, cols)
    for col in cols:
        def transformer(val):
            if pd.isna(val):
                return ""
            val_str = str(val).strip()
            if val_str.lower() in na_values:
                return ""
            return val_str.title()
        df[col] = df[col].apply(transformer)
    return df

# --- Nettoyer : seule la première lettre de la valeur en majuscule ---
def clean_first_letter_only_values(df, cols=None):
    cols = get_target_columns(df, cols)
    for col in cols:
        def transformer(val):
            # Si val est une liste, dict, série, etc., on la convertit en chaîne brute
            if isinstance(val, (list, dict, pd.Series)):
                val = str(val)
            if pd.isna(val):
                return ""
            val_str = str(val).strip()
            if val_str.lower() in na_values:
                return ""
            return val_str.capitalize()
        df[col] = df[col].apply(transformer)
    return df

# --- Nettoyer : mettre toutes les valeurs en majuscules ---
def clean_uppercase_values(df, cols=None):
    cols = get_target_columns(df, cols)
    
    for col in cols:
        def transformer(val):
            if pd.isna(val):
                return pd.NA
            val_str = str(val).strip()
            if val_str.lower() in na_values:
                return pd.NA
            return val_str.upper()
        
        df[col] = df[col].apply(transformer).astype("string")
        
    return df

# --- Supprimer les espaces et nettoyer les valeurs manquantes ---
def clean_all_values(df, cols=None, case_option="none", remove_accents=False, convert_type=True, verbose=False):
    """
    Nettoie les valeurs d'un DataFrame sur les colonnes spécifiées ou toutes si None.

    Actions réalisées :
    - Remplacement des valeurs manquantes définies dans na_values par pd.NA.
    - Suppression des espaces inutiles en début et fin.
    - Suppression des espaces multiples internes.
    - Conversion des valeurs numériques si possible (si convert_type=True).
    - Conversion des dates si possible (si convert_type=True).
    - Option pour transformer la casse des chaînes :
        - 'upper' : mettre en majuscules,
        - 'capitalize' : mettre la première lettre en majuscule, le reste en minuscule,
        - 'lower' : mettre en minuscules,
        - 'title' : première lettre de chaque mot en majuscule,
        - 'none' : ne pas modifier la casse (par défaut).
    - Option pour supprimer les accents (remove_accents=True).
    - Option pour journaliser les colonnes et erreurs (verbose=True).

    Args:
        df (pd.DataFrame) : DataFrame à nettoyer.
        cols (list or str or None) : Colonnes à nettoyer, toutes si None.
        case_option (str) : Option de casse ('upper', 'capitalize', 'lower', 'title', 'none').
        remove_accents (bool) : Supprimer les accents si True.
        convert_type (bool) : Convertir en numérique/date si possible.
        verbose (bool) : Activer les messages de log si True.

    Returns:
        pd.DataFrame : DataFrame nettoyé.
    """
    valid_case_options = {"none", "upper", "capitalize", "lower", "title"}
    if case_option not in valid_case_options:
        raise ValueError(f"case_option doit être l'un de {valid_case_options}")

    case_transforms = {
        "upper": str.upper,
        "capitalize": str.capitalize,
        "lower": str.lower,
        "title": str.title,
        "none": lambda x: x
    }

    cols = get_target_columns(df, cols)

    def clean_val(val):
        if pd.isna(val):
            return pd.NA

        val_str = str(val).strip()

        if val_str.lower() in na_values:
            return pd.NA

        val_str = re.sub(r"\s+", " ", val_str)

        if remove_accents:
            val_str = strip_accents(val_str)

        val_str = case_transforms[case_option](val_str)

        if convert_type:
            try:
                num = pd.to_numeric(val_str)
                return num
            except Exception:
                if verbose:
                    logging.info(f"Conversion numérique échouée : {val_str}")
            try:
                date = pd.to_datetime(val_str, errors='coerce')
                if pd.notna(date):
                    return date.date()
            except Exception:
                if verbose:
                    logging.info(f"Conversion date échouée : {val_str}")

        return val_str

    for col in cols:
        if verbose:
            logging.info(f"Traitement de la colonne : {col}")
        df[col] = df[col].apply(clean_val)

        if convert_type and pd.api.types.is_numeric_dtype(df[col]):
            if pd.api.types.is_float_dtype(df[col]):
                try:
                    df[col] = df[col].astype('Int64')
                except Exception as e:
                    if verbose:
                        logging.info(f"Conversion Int64 échouée sur {col} : {e}")

    return df

# --- Convertir une ou plusieurs colonnes en date ---
def convert_column_to_date(df, colname, date_format=None):

    if isinstance(colname, str):
        colname = [colname]

    for col in colname:
        if col not in df.columns:
            logger.warning(f"Colonne '{col}' non trouvée. Ignorée.")
            continue

        df[col] = df[col].astype(str).str.strip().str.lower()
        df[col] = df[col].replace(na_values, pd.NA)

        try:
            df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce').dt.date
        except Exception as e:
            logger.error(f"Erreur de conversion pour la colonne '{col}': {e}")

    return df

# --- Convertir une ou plusieurs colonnes en date ---
def convert_column_to_date_fast(df, colonnes, lang="all", output="date"):
    """
    Convertit en datetime les colonnes spécifiées (FR/EN).
    
    df : DataFrame
    colonnes : list[str] colonnes à convertir
    lang : "fr" | "en" | "all"
    output : "date" (par défaut) ou "datetime"
    """

    # Formats standards courts
    formats_fr = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]
    formats_en = ["%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y"]

    # Formats longs avec jour et mois textuels (casse insensible, FR & EN)
    formats_long_fr = ["%A %d %B %Y", "%d %B %Y"]
    formats_long_en = ["%A %B %d %Y", "%B %d %Y"]

    if lang == "fr":
        formats_to_try = formats_fr + formats_long_fr
    elif lang == "en":
        formats_to_try = formats_en + formats_long_en
    else:
        formats_to_try = formats_fr + formats_en + formats_long_fr + formats_long_en

    for col in colonnes:
        try:
            # On nettoie un peu (supprime espaces, normalise majuscules/minuscules)
            df[col] = df[col].astype(str).str.strip()

            # Premier essai vectorisé avec pandas
            temp = pd.to_datetime(df[col], errors="coerce", dayfirst=(lang!="en"))

            # Identifier les valeurs encore NaT
            mask = temp.isna() & df[col].notna()

            def safe_parse(x):
                s = str(x).strip()
                # Essai formats explicites
                for fmt in formats_to_try:
                    try:
                        return pd.to_datetime(s, format=fmt, errors="raise")
                    except Exception:
                        continue
                # Fallback puissant : dateutil (gère "lundi 16 Juin 2025" et "Monday June 16 2025")
                try:
                    return parser.parse(s, dayfirst=(lang!="en"))
                except Exception:
                    return pd.NaT

            if mask.any():
                temp.loc[mask] = df.loc[mask, col].apply(safe_parse)

            # Sortie : date simple ou datetime complet
            if output == "date":
                df[col] = temp.dt.date
            else:
                df[col] = temp

            nb_ok = df[col].notna().sum()
            logging.info(f"Colonne '{col}' convertie ({nb_ok}/{len(df[col])} valeurs valides).")

        except Exception as e:
            logging.error(f"Erreur lors de la conversion de la colonne {col}: {e}")

    return df

# --- Convertir float en int si pas de décimale ---
def convert_float_to_int(df, cols=None):
    cols = get_target_columns(df, cols)
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype("Int64")
    return df


# --- Convertir float en int arrondi ---
def convert_float_to_int_arrondi(df, cols=None):
    cols = get_target_columns(df, cols)
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].apply(lambda x: round(x) if pd.notna(x) else pd.NA).astype("Int64")
    return df

# --- Convertir en int arrondi ---
def convertir_en_int(df, colonnes=None):
    """
    Convertit les colonnes données en entier Int64 nullable,
    en arrondissant les floats avant conversion.
    """
    noms_uniques = pd.Series(df.columns).drop_duplicates(keep='first').tolist()

    if colonnes is None:
        colonnes = noms_uniques
    elif isinstance(colonnes, str):
        colonnes = [colonnes]
    else:
        colonnes = [col for col in colonnes if col in noms_uniques]

    for col in colonnes:
        serie = df.loc[:, col]
        if isinstance(serie, pd.DataFrame):
            serie = serie.iloc[:, 0]
        serie_num = pd.to_numeric(serie, errors='coerce')
        # Arrondi et conversion en int nullable
        serie_int = serie_num.round(0).astype('Int64')
        df[col] = serie_int

    return df

# --- Nettoyer les tirets et espaces dans un texte ---
def nettoyer_tiret_et_espaces(texte: str) -> str:
    if not texte:
        return None

    # Remplacer tirets par espaces
    texte = texte.replace("-", " ")

    # Nettoyer espaces multiples
    texte = re.sub(r"\s+", " ", texte).strip()

    # Dictionnaire chiffres romains -> chiffres arabes (seulement I, II, III)
    romain_map = {
        r"\bI\b": "1",
        r"\bII\b": "2",
        r"\bIII\b": "3",
    }

    # Remplacement insensible à la casse
    for romain, arabe in romain_map.items():
        texte = re.sub(romain, arabe, texte, flags=re.IGNORECASE)

    return texte

# Remplacement des underscores et nettoyage d’affichage
def remplacer_underscores(
    df: pd.DataFrame, 
    colonnes: Union[str, List[str]]
) -> pd.DataFrame:
    """
    Remplace _ et - par des espaces dans les colonnes spécifiées.
    Met en minuscules puis applique title() pour chaque mot.
    Garde les NaN inchangés.
    """
    if isinstance(colonnes, str):
        colonnes = [colonnes]

    for col in colonnes:
        if col not in df.columns:
            continue

        df[col] = df[col].apply(
            lambda val: (
                pd.NA if pd.isna(val)
                else str(val).replace('_', ' ').replace('-', ' ').strip().lower().title()
            )
        )

    return df
# Remplacement des espace par des underscores
def remplacer_espaces_par_underscores(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]]
) -> pd.DataFrame:
    """
    Nettoie les colonnes spécifiées en :
    - supprimant les espaces en début/fin
    - remplaçant tous les espaces internes (même multiples) par un seul underscore
    - supprimant les underscores multiples éventuels
    - capitalisant chaque mot séparé par underscore
    - conservant les NaN inchangés
    """
    if isinstance(colonnes, str):
        colonnes = [colonnes]

    for col in colonnes:
        if col not in df.columns:
            continue

        def transformer(val):
            if pd.isna(val):
                return pd.NA

            # Convertir en string et enlever les espaces début/fin
            val = str(val).strip()

            # Remplacer tous les groupes d'espaces internes par un seul underscore
            val = re.sub(r'\s+', '_', val)

            # Nettoyer les underscores multiples éventuels
            val = re.sub(r'_+', '_', val)

            # Split sur les underscores, capitalize chaque mot, re-joindre
            mots = val.split('_')
            mots_capitalises = [mot.capitalize() for mot in mots if mot]
            return '_'.join(mots_capitalises)

        df[col] = df[col].apply(transformer)

    return df


# ----------------------------------------------------------
# --- Découpage des valeurs : Prefixe, nom et Suffixe ---
# ----------------------------------------------------------

## --- Prefixe fixe ---
def trouve_caractere(provenance: str, valeur_avant: str, valeur_apres: str) -> str:
    """
    Extrait la sous-chaîne comprise entre `valeur_avant` et `valeur_apres`.

    Args:
        provenance (str): La valeur complète (ex: 'LLCholera_DPS_KIN_SE33_20250819')
        valeur_avant (str): La chaîne qui précède la valeur recherchée (ex: 'DPS_')
        valeur_apres (str): La chaîne qui suit la valeur recherchée (ex: 'SE33')

    Returns:
        str: La valeur extraite (ex: 'KIN') ou '' si non trouvée.
    """
    try:
        start = provenance.index(valeur_avant) + len(valeur_avant)
        end = provenance.index(valeur_apres, start)
        return provenance[start:end]
    except ValueError:
        # Si l'un des motifs n'existe pas
        return ""


## --- Prefixe fixe ---
def extraire_prefixe(texte: str, longueur: int = 1, mode: str = "mot") -> str:
    """
    Extrait un préfixe depuis une chaîne selon le mode choisi :
    - 'mot' : extrait les n premiers mots.
    - 'caractere' : extrait les n premiers caractères.

    Args:
        texte (str): La chaîne à traiter.
        longueur (int): Nombre de mots ou de caractères à extraire.
        mode (str): Mode d'extraction, 'mot' ou 'caractere'.

    Returns:
        str: Le préfixe extrait ou None si texte vide ou invalide.
    """
    if not texte:
        return None

    texte = texte.strip()

    if mode == "mot":
        mots = texte.split()
        return " ".join(mots[:longueur]) if mots else None

    elif mode == "caractere":
        return texte[:longueur]

    else:
        raise ValueError("Le paramètre 'mode' doit être 'mot' ou 'caractere'")

## --- Nom ---
def extraire_nom_generique(texte: str) -> str:
    """
    Extrait le 'nom générique' dans un libellé administratif ou sanitaire.

    Règles :
    - Ignore le préfixe (premier mot).
    - Supprime les suffixes connus (province, zone de santé, etc.) insensibles à la casse.
    - Retourne le reste comme nom générique.

    Args:
        texte (str): Le libellé à nettoyer.

    Returns:
        str: Le nom extrait ou None si introuvable.
    """
    if not texte:
        return None

    mots = texte.strip().split()
    if len(mots) <= 2:
        return None

    # Retirer le préfixe (premier mot)
    mots = mots[1:]

    # Liste des suffixes connus à retirer
    mots_a_enlever_fin = {
        "province",
        "zone de santé",
        "zone de sante",
        "aire de santé",
        "aire de sante",
        "centre de santé",
        "centre de sante",
        "dispensaire",
        "centre de santé de référence"
    }

    # Boucle pour retirer suffixes connus à la fin
    while mots:
        max_suffix_len = min(4, len(mots))
        suffixe_trouve = False

        # Tester du plus long suffixe possible vers le plus court
        for l in range(max_suffix_len, 0, -1):
            fin = " ".join(mots[-l:]).lower()
            if fin in mots_a_enlever_fin:
                for _ in range(l):
                    mots.pop()
                suffixe_trouve = True
                break

        if not suffixe_trouve:
            break

    if not mots:
        return None

    return " ".join(mots)


## --- Suffixe ---
def extraire_suffixe(texte: str, longueur: int = 1, mode: str = "mot") -> str:
    """
    Extrait un suffixe depuis une chaîne selon le mode choisi :
    - 'mot' : extrait les n derniers mots.
    - 'caractere' : extrait les n derniers caractères.

    Args:
        texte (str): La chaîne à traiter.
        longueur (int): Nombre de mots ou de caractères à extraire.
        mode (str): Mode d'extraction, 'mot' ou 'caractere'.

    Returns:
        str: Le suffixe extrait ou None si texte vide ou invalide.
    """
    if not texte:
        return None

    texte = texte.strip()

    if mode == "mot":
        mots = texte.split()
        return " ".join(mots[-longueur:]) if mots else None

    elif mode == "caractere":
        return texte[-longueur:] if len(texte) > 0 else None

    else:
        raise ValueError("Le paramètre 'mode' doit être 'mot' ou 'caractere'")


# Extraire texte et nombre d'une cellule ou d'une liste de cellules
def extraire_texte_et_nombre(
    cellule: Union[str, int, float, List[Union[str, int, float]]],
    valeur_par_defaut: str = "mois",
    detecter_annee: bool = True,
    normaliser_texte: bool = True,
    mode: str = "both"  # "texte", "nombre", "both"
) -> Union[str, int, dict, List[Union[str, int, dict]]]:
    """
    Extrait texte et/ou nombre depuis une chaîne, un nombre ou une liste,
    avec logging de la valeur brute + extraction sur une seule ligne.

    Args:
        cellule (str | int | float | list): Valeur(s) à analyser.
        valeur_par_defaut (str): Unité par défaut.
        detecter_annee (bool): Détecte les variantes d'"année".
        normaliser_texte (bool): Normalise les unités.
        mode (str): "texte", "nombre" ou "both".

    Returns:
        str/int/dict ou liste selon mode.
    """

    def detecter_unite_et_nombre(elem_str):
        elem_str = elem_str.lower().strip()

        pattern_annee = r"\b(an|ans|année|années|a)\b"
        pattern_mois = r"\b(mois|moi|m)\b"
        pattern_jour = r"\b(jour|jours|jr|jrs|j)\b"

        if detecter_annee and re.search(pattern_annee, elem_str):
            unite = "ans" if normaliser_texte else re.search(pattern_annee, elem_str).group(0)
        elif re.search(pattern_mois, elem_str):
            unite = "mois"
        elif re.search(pattern_jour, elem_str):
            unite = "jours"
        else:
            match_abrev = re.search(r"(\d+)\s*([amj])\b", elem_str)
            if match_abrev:
                lettre = match_abrev.group(2)
                unite = {"a": "ans", "m": "mois", "j": "jours"}.get(lettre, valeur_par_defaut)
            else:
                unite = valeur_par_defaut

        match_nombre = re.search(r"\d+", elem_str)
        nombre = int(match_nombre.group(0)) if match_nombre else None

        if elem_str.isdigit():
            unite = valeur_par_defaut
            nombre = int(elem_str)

        return unite, nombre

    def traiter_element(elem):
        if pd.isna(elem):
            texte = valeur_par_defaut
            nombre = None
        else:
            elem_str = str(elem).strip()
            texte, nombre = detecter_unite_et_nombre(elem_str)

        logger.info(f"[Extraction] Valeur brute: {elem!r} | Texte: {texte} | Nombre: {nombre}")

        if mode == "texte":
            return texte
        elif mode == "nombre":
            return nombre
        else:  # mode == "both"
            return {"texte": texte, "nombre": nombre}

    if isinstance(cellule, list):
        return [traiter_element(e) for e in cellule]
    else:
        return traiter_element(cellule)

# ----------------------------------------------------------
# --- Fonction principale de nettoyage global des valeurs ---
# ----------------------------------------------------------

def clean_all_values_names(df):
    df = replace_specific_values(df) # Remplacer des valeurs selon un mapping Excel
    df = clean_all_values(df) # Supprimer les espaces et nettoyer les valeurs manquantes
    return df

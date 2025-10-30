# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/colonne_remplissage.py

# Notice : Remplissage de valeurs par colonnes bien définies de df

import pandas as pd
import numpy as np
import logging
import unicodedata
from pathlib import Path
from rapidfuzz import fuzz, process
import re
from typing import Union, List, Dict

from dataminsante.database.database_pyramide import lire_excel_secure,clean_database_pyramide

# Configuration du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Chemin dynamique basé sur le dossier courant 
base_dir = Path(__file__).resolve().parents[2] / "data"
mapping_file_path = base_dir / "rdc_database_pyramide_code.xlsx"
database_pyramide=lire_excel_secure(mapping_file_path)

# ----------------------------------------------------------
# Fonction générique
# ----------------------------------------------------------

def creer_dictionnaire(df_ref, colonne_source, colonne_cible, normaliser=False):
    """
    Crée un dictionnaire de correspondance df_ref[colonne_source] -> df_ref[colonne_cible].
    
    Args:
        df_ref (pd.DataFrame)
        colonne_source (str): Colonne source dans df_ref
        colonne_cible (str): Colonne cible dans df_ref
        normaliser (bool): Applique normaliser_chaine sur les valeurs source et cible
        
    Returns:
        dict: mapping
    Exemple :
    # Créer les dictionnaires
    dico_zone = creer_dictionnaire(pyramide, "Code_zone_de_sante", "Zone_de_sante")
    dico_aire = creer_dictionnaire(pyramide, "Aire_de_sante", "Zone_de_sante")
    
    """
    if normaliser:
        clefs = df_ref[colonne_source].dropna()
        valeurs = df_ref[colonne_cible].dropna().apply(normaliser_chaine)
    else:
        clefs = df_ref[colonne_source].dropna()
        valeurs = df_ref[colonne_cible].dropna()
    return dict(zip(clefs, valeurs))

def ajouter_colonnes_manquantes(df: pd.DataFrame, colonnes, valeur_defaut=None) -> pd.DataFrame:
    """
    Ajoute dans le DataFrame les colonnes manquantes parmi une liste donnée.
    - Si une colonne n'existe pas, elle est créée avec une valeur par défaut.
    - Si la colonne existe déjà, elle est laissée telle quelle.

    Args:
        df (pd.DataFrame): Le DataFrame à compléter.
        colonnes (list ou str): Liste de noms de colonnes (ou une seule colonne).
        valeur_defaut (any, optionnel): Valeur à mettre dans les colonnes créées. 
                                        Par défaut None.

    Returns:
        pd.DataFrame: Le DataFrame complété avec toutes les colonnes.
    """
    if isinstance(colonnes, str):
        colonnes = [colonnes]

    colonnes_creees = []

    for col in colonnes:
        if col not in df.columns:
            df[col] = valeur_defaut
            colonnes_creees.append(col)

    if colonnes_creees:
        logger.info(f"Colonnes ajoutées automatiquement : {sorted(colonnes_creees)}")

    return df

# Initialisation des dictionnaires de correspondance
pyramide = clean_database_pyramide()

# ----------------------------------------------------------
# Provinces et zones de santé
# ----------------------------------------------------------
## Provinces et zones
def normaliser_chaine(s: str) -> str:
    """
    Normalise une chaîne pour les noms de province/zone :
    - strip (espaces en trop)
    - suppression des accents
    - remplacement de "_" et "-" par un espace
    - suppression des doubles espaces
    - première lettre de chaque mot en majuscule
    """
    if pd.isna(s):
        return None
    
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r'\s+', ' ', s)
    s = s.title()
    return s

def creer_dictionnaires_pyramide(df_ref=clean_database_pyramide(), normaliser=True):
    """
    Construit automatiquement les dictionnaires de correspondance Province / Zone / Aire.
    Les clés des dictionnaires sont en majuscules.

    Paramètres
    ----------
    df_ref : pd.DataFrame, optionnel
        DataFrame pyramide contenant au minimum les colonnes :
        ['Province', 'Code_Province', 'Zone_de_sante', 'Code_zone_de_sante', 'Aire_de_sante'].
    normaliser : bool, optionnel (default=True)
        Applique `normaliser_chaine` sur les valeurs pour uniformisation.

    Retour
    ------
    dict
        Dictionnaires par type de référence :
        - "N_epid" : Code_Province -> Province
        - "Zone_de_sante" : Zone_de_sante -> Province
        - "Aire_de_sante" : Aire_de_sante -> Province
        - "Code_zone" : Code_zone_de_sante -> Zone_de_sante
    """
    dicos = {
        "N_epid": {},        # Code Province -> Province
        "Zone_de_sante": {}, # Zone -> Province
        "Aire_de_sante": {}, # Aire -> Province
        "Code_zone": {}      # Code_zone -> Zone
    }

    _norm = lambda s: normaliser_chaine(s) if normaliser else s

    # Province
    if "Code_Province" in df_ref.columns and "Province" in df_ref.columns:
        dicos["N_epid"] = dict(zip(
            df_ref["Code_Province"].dropna().astype(str).map(lambda x: _norm(x).upper()),
            df_ref["Province"].dropna().map(_norm)
        ))

    # Zone_de_sante -> Province
    if "Zone_de_sante" in df_ref.columns and "Province" in df_ref.columns:
        dicos["Zone_de_sante"] = dict(zip(
            df_ref["Zone_de_sante"].dropna().map(lambda x: _norm(x).upper()),
            df_ref["Province"].dropna().map(_norm)
        ))

    # Aire_de_sante -> Province
    if "Aire_de_sante" in df_ref.columns and "Province" in df_ref.columns:
        dicos["Aire_de_sante"] = dict(zip(
            df_ref["Aire_de_sante"].dropna().map(lambda x: _norm(x).upper()),
            df_ref["Province"].dropna().map(_norm)
        ))

    # Code_zone_de_sante -> Zone_de_sante
    if "Code_zone_de_sante" in df_ref.columns and "Zone_de_sante" in df_ref.columns:
        dicos["Code_zone"] = dict(zip(
            df_ref["Code_zone_de_sante"].dropna().astype(str).map(lambda x: _norm(x).upper()),
            df_ref["Zone_de_sante"].dropna().map(_norm)
        ))

    return dicos

def remplir_colonne_depuis_reference(
    df: pd.DataFrame,
    colonne_a_remplir: str,
    colonne_reference: Union[str, List[str]],
    type_reference: str,
    dictionnaires: Dict[str, Dict[str, str]],
    variable_remplissage: str = "Province",
    log_erreurs: bool = True,
    normaliser: bool = True
) -> pd.DataFrame:
    """
    Remplit une colonne d'un DataFrame à partir d'une ou plusieurs colonnes de référence.
    
    Fonction compatible avec plusieurs colonnes de référence :
    - N_epid_prov (code province en tête)
    - N_epid (code pays en tête)

    Cherche le code zone ou province dans les dictionnaires en fallback.

    Paramètres
    ----------
    df : pandas.DataFrame
        Le DataFrame à traiter.
    colonne_a_remplir : str
        Colonne cible à remplir.
    colonne_reference : str ou list
        Colonnes de référence pour le mapping (ordre = priorité).
    type_reference : str
        Type de référence pour dictionnaire ("N_epid", "Zone_de_sante", etc.).
    dictionnaires : dict
        Dictionnaires de correspondance (clés en majuscules).
    variable_remplissage : str, optionnel
        "Province" ou "Zone_de_sante".
    log_erreurs : bool, optionnel
        Affiche les valeurs non trouvées si True.
    normaliser : bool, optionnel
        Normalise les valeurs avant recherche si True.

    Retour
    ------
    pd.DataFrame
        DataFrame avec la colonne mise à jour.
    """
    df = df.copy()
    if isinstance(colonne_reference, str):
        colonnes_ref = [colonne_reference]
    else:
        colonnes_ref = colonne_reference

    colonnes_ref_existantes = [c for c in colonnes_ref if c in df.columns]
    if not colonnes_ref_existantes:
        logging.info(f"⚠ Aucune colonne de référence existante parmi {colonnes_ref}")
        return df

    initial_non_null = df[colonne_a_remplir].notna()

    def mapper(row):
        for col in colonnes_ref_existantes:
            val = row[col]
            if pd.isna(val):
                continue

            val_norm = normaliser_chaine(val) if normaliser else val
            parts = str(val).split("-")

            # Remplissage Province
            if variable_remplissage == "Province":
                if type_reference == "N_epid":
                    if col == "N_epid" and len(parts) >= 2:
                        code_prov = parts[1].upper()
                    elif col == "N_epid_prov" and len(parts) >= 1:
                        code_prov = parts[0].upper()
                    else:
                        code_prov = None
                    if code_prov:
                        province = dictionnaires.get("Province", {}).get(code_prov)
                        if province:
                            return province
                else:
                    province = dictionnaires.get(type_reference, {}).get(val_norm)
                    if province:
                        return province

            # Remplissage Zone de santé
            elif variable_remplissage == "Zone_de_sante":
                code_zone = None
                if type_reference == "N_epid":
                    if col == "N_epid" and len(parts) >= 3:
                        code_zone = parts[2].upper()
                    elif col == "N_epid_prov" and len(parts) >= 2:
                        code_zone = parts[1].upper()
                if code_zone:
                    zone = dictionnaires.get("Code_zone", {}).get(code_zone)
                    if zone:
                        return zone
                else:
                    zone = dictionnaires.get(type_reference, {}).get(val_norm)
                    if zone:
                        return zone

        return None

    df["_temp"] = df.apply(mapper, axis=1)
    df[colonne_a_remplir] = df[colonne_a_remplir].fillna(df["_temp"])

    nb_remplis = (df[colonne_a_remplir].notna() & ~initial_non_null).sum()
    logging.info(f"✅ {nb_remplis} valeurs remplies ou remplacées dans '{colonne_a_remplir}'")

    if log_erreurs:
        non_trouves = df["_temp"].isna() & df[colonne_a_remplir].isna()
        if non_trouves.any():
            valeurs = df.loc[non_trouves, colonnes_ref_existantes].apply(
                lambda x: "|".join([str(i) for i in x if pd.notna(i)]), axis=1
            ).unique()
            logging.info(f"⚠ Références non trouvées pour {type_reference}: {list(valeurs[:10])} …")

    df.drop(columns=["_temp"], inplace=True)
    return df

def nettoyer_colonnes(
    df_dirty: pd.DataFrame,
    df_ref: pd.DataFrame,
    col_dirty_boucle: str,                # colonne de regroupement dans df_dirty
    cols_a_nettoyer: list = None,         # colonnes à corriger dans df_dirty
    mapping_colonnes: dict = None,        # dict {col_df_dirty: col_df_ref}
    code_mapping: dict = None,            # dict {col_df_ref: col_code} ex {"Zone_de_sante": "Code_zone_de_sante"}
    seuil: int = 90
) -> pd.DataFrame:
    """
    Nettoie et harmonise les valeurs de colonnes dans un DataFrame "df_dirty" en se basant sur un DataFrame
    de référence "df_ref".

    La fonction applique la logique suivante pour chaque colonne à corriger :

    1. Parcours des valeurs de la colonne de regroupement (`col_dirty_boucle`) dans df_dirty.
       Cela permet de traiter les sous-ensembles correspondant à chaque valeur unique (ex: Province).

    2. Pour chaque valeur à corriger :
       a. Vérification exacte avec les valeurs de df_ref.
       b. Si une colonne code est définie dans `code_mapping`, tentative de correction via code.
       c. Si aucune correspondance exacte ou code, correction via fuzzy matching (RapidFuzz) si le score >= `seuil`.

    Paramètres
    ----------
    df_dirty : pd.DataFrame
        Le DataFrame contenant les données à nettoyer.
    df_ref : pd.DataFrame
        Le DataFrame de référence servant à corriger les valeurs.
    col_dirty_boucle : str
        Nom de la colonne dans df_dirty utilisée pour regrouper les lignes avant nettoyage
        (ex: "Province_notification"). La fonction traitera chaque groupe séparément.
    cols_a_nettoyer : list, optionnel
        Liste des colonnes de df_dirty à corriger.
    mapping_colonnes : dict, optionnel
        Dictionnaire de correspondance {col_df_dirty: col_df_ref} indiquant pour chaque colonne
        de df_dirty la colonne correspondante dans df_ref.
    code_mapping : dict, optionnel
        Dictionnaire {col_df_ref: col_code} indiquant pour chaque colonne de df_ref la colonne code
        pouvant servir pour la correction exacte.
    seuil : int, optionnel (défaut=80)
        Score minimal de similarité pour appliquer le fuzzy matching (0-100).

    Retour
    ------
    pd.DataFrame
        Une copie de df_dirty avec les valeurs corrigées pour les colonnes spécifiées.

    Notes
    -----
    - Les colonnes de regroupement et de référence doivent exister dans les DataFrames correspondants.
    - Les valeurs NaN dans df_dirty sont ignorées.
    - Les logs détaillent les corrections effectuées (via code ou fuzzy matching).
    """
    
    if cols_a_nettoyer is None or mapping_colonnes is None:
        raise ValueError("⚠️ Vous devez définir cols_a_nettoyer et mapping_colonnes")

    df_corr = df_dirty.copy()

    # Détection des colonnes dupliquées ou absentes
    colonnes_dupliquees = [col for col in cols_a_nettoyer if cols_a_nettoyer.count(col) > 1]
    colonnes_absentes = [col for col in cols_a_nettoyer if col not in df_corr.columns]

    if colonnes_dupliquees:
        logging.info(f"Colonnes dupliquées ignorées : {sorted(set(colonnes_dupliquees))}")
    if colonnes_absentes:
        logging.warning(f"Colonnes absentes ignorées : {sorted(colonnes_absentes)}")

    # On ne garde que les colonnes réellement présentes pour le traitement
    cols_a_traiter = [col for col in cols_a_nettoyer if col in df_corr.columns]

    # Détection de la colonne correspondante dans df_ref
    col_ref_df_ref = mapping_colonnes.get(col_dirty_boucle, col_dirty_boucle)
    if col_ref_df_ref not in df_ref.columns:
        raise KeyError(f"⚠️ La colonne {col_ref_df_ref} n'existe pas dans df_ref")

    # Boucle par regroupement
    for valeur_ref in df_corr[col_dirty_boucle].dropna().unique():
        ref_subset = df_ref[df_ref[col_ref_df_ref] == valeur_ref]
        df_subset = df_corr[df_corr[col_dirty_boucle] == valeur_ref]

        for idx, row in df_subset.iterrows():
            for col_dirty in cols_a_traiter:
                col_ref = mapping_colonnes.get(col_dirty)
                if col_ref is None or col_ref not in df_ref.columns:
                    logging.warning(f"⚠️ Pas de correspondance trouvée pour {col_dirty} -> {col_ref}")
                    continue

                valeur = row[col_dirty]
                if pd.isna(valeur):
                    continue

                # Vérification exacte
                if valeur not in ref_subset[col_ref].values:
                    # Tentative via code si code_mapping fourni
                    code_col = code_mapping.get(col_ref) if code_mapping else None

                    if (
                        code_col
                        and code_col in ref_subset.columns
                        and code_col in df_corr.columns
                    ):
                        correct_val = ref_subset.loc[
                            ref_subset[code_col] == row.get(code_col, None),
                            col_ref
                        ]
                        if not correct_val.empty:
                            df_corr.at[idx, col_dirty] = correct_val.values[0]
                            logging.info(
                                f"[{col_dirty}] Correction via code: {valeur} -> {correct_val.values[0]}"
                            )
                            continue

                    # Sinon fuzzy matching
                    choix = process.extractOne(
                        valeur,
                        ref_subset[col_ref].dropna().unique(),
                        scorer=fuzz.ratio
                    )
                    if choix and choix[1] >= seuil:
                        df_corr.at[idx, col_dirty] = choix[0]
                        logging.info(
                            f"[{col_dirty}] Correction fuzzy: {valeur} -> {choix[0]} (score {choix[1]})"
                        )

    return df_corr

# ----------------------------------------------------------
# Age, tranches d'âge et unites age
# ----------------------------------------------------------

# Création de tranches d'âge paramétrables
def creer_tranche_age(
    df: pd.DataFrame,
    col_reference: str = 'Age',
    mode: str = '10ans',
    col_tranche: str = 'Tranche_age',
    age_max: int = 65
) -> pd.DataFrame:
    """
    Ajoute une colonne 'Tranche_age' avec des intervalles paramétrables (5ans ou 10ans) et une borne supérieure personnalisée.

    Args:
        df (pd.DataFrame): DataFrame d'entrée.
        col_reference (str): Colonne d'âge à découper.
        mode (str): '5ans' ou '10ans'.
        col_tranche (str): Nom de la colonne de sortie.
        age_max (int): Âge maximum regroupé dans la dernière tranche.

    Returns:
        pd.DataFrame: DataFrame avec colonne 'Tranche_age' ajoutée.
    """
    col_reference = col_reference.strip()
    if col_reference not in df.columns:
        logger.warning(f"❗ Colonne '{col_reference}' absente du DataFrame.")
        return df

    # Vérifier et convertir en numérique
    if not pd.api.types.is_numeric_dtype(df[col_reference]):
        try:
            df[col_reference] = pd.to_numeric(df[col_reference], errors='coerce')
            logger.info(f"✅ Colonne '{col_reference}' convertie en numérique.")
        except Exception as e:
            logger.error(f"❌ Impossible de convertir '{col_reference}' en numérique : {e}")
            return df

    # Remplacer valeurs supérieures à age_max par age_max
    df[col_reference] = df[col_reference].clip(upper=age_max)

    # Définition dynamique des bornes et labels
    pas = 5 if mode == '5ans' else 10 if mode == '10ans' else None
    if pas is None:
        logger.warning(f"❗ Mode '{mode}' non reconnu. Choisir '5ans' ou '10ans'.")
        return df

    bins = list(range(0, age_max, pas)) + [age_max]
    labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-2)] + [f"{bins[-2]}+"]

    try:
        df[col_tranche] = pd.cut(
            df[col_reference],
            bins=bins,
            labels=labels,
            right=True,
            include_lowest=True
        )
        logger.info(f"✅ Colonne {col_tranche} ajoutée (mode: {mode}, age_max: {age_max}).")
    except Exception as e:
        logger.error(f"❌ Erreur lors du découpage en tranches d'âge : {e}")

    return df

# Nettoyage unite age
def nettoyer_unite_age(df: pd.DataFrame, col='Unite_age', nouvelle_colonne=None) -> pd.DataFrame:
    """
    Nettoie et standardise la colonne 'Unite_age' en valeurs 'ans', 'mois', 'semaine' ou NaN.
    
    Args:
        df (pd.DataFrame): DataFrame d'entrée
        col (str): Nom de la colonne à nettoyer
        nouvelle_colonne (str): Nom de la colonne résultat. Si None, remplace col.

    Returns:
        pd.DataFrame: DataFrame avec colonne nettoyée.
    """

    if col not in df.columns:
        raise ValueError(f"Colonne '{col}' non trouvée dans le DataFrame.")

    # Copie pour transformation
    serie = df[col].copy()

    # Tout en str, lower, strip
    serie = serie.astype(str).str.lower().str.strip()

    # Nettoyer variantes évidentes
    serie = serie.replace({
        'années': 'ans',
        'annee': 'ans',
        'année': 'ans',
        'ans ': 'ans',
        'ans': 'ans',
        'an': 'ans',
        'a': 'ans',
        'm': 'mois',
        'mm': 'mois',
        'mos': 'mois',
        'mois ': 'mois',
        'mois': 'mois',
        'mo': 'mois',
        'semaine': 'semaine'
    })

    # Détecter présence explicite
    serie = serie.apply(
        lambda x: 'ans' if 'ans' in x or 'an' in x else
                  'mois' if 'mois' in x or 'm ' in x or 'm' == x else
                  'semaine' if 'semaine' in x else x
    )

    # Essayer de gérer les nombres seuls
    def standardiser_numerique(val):
        try:
            num = float(val)
            if num < 12:
                return 'mois'
            elif num < 120:
                return 'ans'
        except:
            return val
        return val

    serie = serie.apply(standardiser_numerique)

    # Nettoyer tout ce qui n'est pas dans nos catégories finales
    serie = serie.where(serie.isin(['ans', 'mois', 'semaine']), np.nan)

    # Affecter au DataFrame
    if nouvelle_colonne is None:
        df[col] = serie
    else:
        df[nouvelle_colonne] = serie

    return df

# Créer tranche âge avec unité et borne max
def creer_tranche_age_avec_unite(
    df: pd.DataFrame,
    col_age: str = 'Age',
    col_unite: str = 'Unite_age',
    mode: str = '10ans',
    col_tranche: str = 'Tranche_age',
    age_max: int = 65
) -> pd.DataFrame:
    """
    Ajoute une colonne 'Tranche_age' en tenant compte de l'unité (ans, mois, semaine)
    avec possibilité de définir la borne supérieure.

    Args:
        df (pd.DataFrame): DataFrame d'entrée.
        col_age (str): Nom de la colonne contenant la valeur d'âge.
        col_unite (str): Nom de la colonne indiquant l'unité ('ans', 'mois', 'semaine').
        mode (str): '5ans' ou '10ans'.
        col_tranche (str): Nom de la colonne de sortie.
        age_max (int): Âge maximum regroupé dans la dernière tranche.

    Returns:
        pd.DataFrame: DataFrame enrichi avec la colonne 'Tranche_age'.
    """
    # Vérifier les colonnes
    if col_age not in df.columns:
        logger.warning(f"❗ Colonne '{col_age}' absente du DataFrame.")
        return df

    if col_unite not in df.columns:
        logger.warning(f"❗ Colonne '{col_unite}' absente du DataFrame.")
        return df

    # Convertir Age en numérique
    df[col_age] = pd.to_numeric(df[col_age], errors='coerce')

    # Harmoniser Age en années
    def convertir_en_ans(row):
        age = row[col_age]
        unite = str(row[col_unite]).strip().lower() if pd.notna(row[col_unite]) else None
        if pd.isna(age) or not unite:
            return np.nan
        if unite in ('ans', 'annee', 'années','annees'):
            return age
        elif unite in ('mois', 'mois(s)'):
            return age / 12
        elif unite in ('semaine', 'semaines'):
            return age / 52
        return np.nan

    df['Age_en_ans'] = df.apply(convertir_en_ans, axis=1)

    # Remplacer valeurs supérieures à age_max par age_max
    df['Age_en_ans'] = df['Age_en_ans'].clip(upper=age_max)

    # Définition dynamique des bins et labels
    pas = 5 if mode == '5ans' else 10 if mode == '10ans' else None
    if pas is None:
        logger.warning(f"❗ Mode '{mode}' non reconnu. Choisir '5ans' ou '10ans'.")
        return df

    bins = list(range(0, age_max, pas)) + [age_max]
    labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-2)] + [f"{bins[-2]}+"]

    # Découper en tranches
    try:
        df[col_tranche] = pd.cut(
            df['Age_en_ans'],
            bins=bins,
            labels=labels,
            right=True,
            include_lowest=True
        )
        logger.info(f"✅ Colonne {col_tranche} ajoutée (mode: {mode}, age_max: {age_max}).")
    except Exception as e:
        logger.error(f"❌ Erreur lors du découpage en tranches d'âge : {e}")

    return df

def creer_tranche_age_avec_unite_generique(
    df: pd.DataFrame,
    col_age: str = 'Age',
    col_unite: str = 'Unite_age'
) -> pd.DataFrame:
    """
    Ajoute une colonne 'Tranche_age' selon les tranches d'âge spécifiques définies.

    Tranches définies :
      - 0-11 mois
      - 12-59 mois
      - 5-15 ans
      - >15 ans

    Args:
        df (pd.DataFrame): DataFrame d'entrée.
        col_age (str): Colonne avec la valeur d'âge.
        col_unite (str): Colonne indiquant l'unité ('ans', 'mois', 'semaine').

    Returns:
        pd.DataFrame: DataFrame avec la colonne 'Tranche_age' ajoutée.
    """

    if col_age not in df.columns:
        logger.warning(f"❗ Colonne '{col_age}' absente du DataFrame.")
        return df

    if col_unite not in df.columns:
        logger.warning(f"❗ Colonne '{col_unite}' absente du DataFrame.")
        return df

    # Nettoyage
    df[col_age] = pd.to_numeric(df[col_age], errors='coerce')
    df[col_unite] = df[col_unite].str.lower().str.strip()

    def assigner_tranche(row):
        age = row[col_age]
        unite = row[col_unite]

        if pd.isna(age) or pd.isna(unite):
            return np.nan

        if unite == "mois":
            if 0 <= age <= 11:
                return "0-11 mois"
            elif 12 <= age <= 59:
                return "12-59 mois"
            else:
                return ">59 mois"

        elif unite in ('ans', 'annee', 'années','annees'):
            if 5 <= age <= 15:
                return "5-15 ans"
            elif age > 15:
                return ">15 ans"
            else:
                return "<5 ans"

        else:
            return "Unité inconnue"

    df['Tranche_age'] = df.apply(assigner_tranche, axis=1)

    logger.info("✅ Colonne 'Tranche_age' ajoutée avec la catégorisation personnalisée.")

    return df

# Fusionner les colonnes d'âge en années et en mois
def fusionner_colonnes_Age_annee_Age_mois(
    df: pd.DataFrame,
    col_age_annee: str = "Age_annee",
    col_age_mois: str = "Age_mois",
    nom_colonne_age: str = "Age",
    nom_colonne_unite: str = "Unite_age",
    age_limite_en_annees: float = 5.0,
    arrondi_mois: int = 1,
    arrondi_annees: int = 2,
    drop_originals: bool = False
) -> pd.DataFrame:
    """
    Fusionne deux colonnes représentant l'âge en années et en mois pour créer une
    colonne d'âge unifiée, ainsi qu'une colonne indiquant l'unité correspondante.

    La fonction effectue les étapes suivantes :
        - Convertit les colonnes source en float (valeurs invalides transformées en NaN).
        - Remplace temporairement les NaN par 0 pour le calcul.
        - Calcule l'âge total en années à partir des colonnes année et mois.
        - Remplace les valeurs impossibles (négatives ou >120 ans / >1440 mois) par NaN.
        - Détermine l'unité de sortie ("mois" si âge < `age_limite_en_annees`, sinon "annees").
        - Crée la colonne `nom_colonne_age` :
            * Âge en mois si unité = "mois" (arrondi à `arrondi_mois`)
            * Âge en années si unité = "annees" (arrondi à `arrondi_annees`)
        - Affiche un warning si des valeurs invalides ont été remplacées par NaN.
        - Optionnellement supprime les colonnes sources (`drop_originals=True`).

    Args:
        df (pd.DataFrame): DataFrame d'entrée contenant les colonnes d'âge.
        col_age_annee (str): Nom de la colonne contenant l'âge en années.
        col_age_mois (str): Nom de la colonne contenant l'âge en mois.
        nom_colonne_age (str): Nom de la colonne fusionnée à créer.
        nom_colonne_unite (str): Nom de la colonne indiquant l'unité de l'âge.
        age_limite_en_annees (float): Seuil en années pour décider de l'unité ("mois" ou "annees").
        arrondi_mois (int): Nombre de décimales pour les valeurs en mois.
        arrondi_annees (int): Nombre de décimales pour les valeurs en années.
        drop_originals (bool): Supprimer les colonnes sources si True.

    Returns:
        pd.DataFrame: DataFrame enrichi avec les colonnes fusionnées `nom_colonne_age` 
                      et `nom_colonne_unite`.

    Raises:
        ValueError: Si l'une des colonnes source est absente du DataFrame.

    Exemple:
        >>> df = pd.DataFrame({
        ...     "Age_annee": [0, 1, 2, None],
        ...     "Age_mois": [6, 18, None, 30]
        ... })
        >>> fusionner_colonnes_Age_annee_Age_mois(df)
           Age_annee  Age_mois   Age Unite_age
        0        0.0       6.0   6.0      mois
        1        1.0      18.0  30.0      mois
        2        2.0       NaN   2.0    annees
        3        NaN      30.0  30.0      mois
    """

    df = df.copy()

    # Validation : les colonnes doivent exister
    for col in [col_age_annee, col_age_mois]:
        if col not in df.columns:
            raise ValueError(f"Colonne absente dans le DataFrame : '{col}'")

    # Conversion sécurisée des valeurs en float (coerce = NaN si invalide)
    df[col_age_annee] = pd.to_numeric(df[col_age_annee], errors="coerce")
    df[col_age_mois] = pd.to_numeric(df[col_age_mois], errors="coerce")

    # Remplacer NaN par 0 pour le calcul
    age_annee = df[col_age_annee].fillna(0)
    age_mois = df[col_age_mois].fillna(0)

    # Calcul de l'âge total en années
    age_total_annees = age_annee + (age_mois / 12)

    # Gestion des valeurs impossibles
    age_total_annees = age_total_annees.where((age_total_annees >= 0) & (age_total_annees <= 120))
    age_annee = age_annee.where((age_annee >= 0) & (age_annee <= 120))
    age_mois = age_mois.where((age_mois >= 0) & (age_mois <= 1440))  # 120 ans en mois

    # Déterminer l'unité
    df[nom_colonne_unite] = np.where(age_total_annees < age_limite_en_annees, "mois", "annees")

    # Calcul de la colonne Age
    df[nom_colonne_age] = np.where(
        df[nom_colonne_unite] == "mois",
        (age_annee * 12 + age_mois).round(arrondi_mois),
        age_total_annees.round(arrondi_annees)
    )

    # Log des valeurs invalides remplacées par NaN
    nb_invalides = df[nom_colonne_age].isna().sum()
    if nb_invalides > 0:
        logger.warning(f"[fusionner_colonnes_age] {nb_invalides} âge(s) invalide(s) détecté(s) et remplacé(s) par NaN")

    # Optionnel : suppression des colonnes sources
    if drop_originals:
        df.drop(columns=[col_age_annee, col_age_mois], inplace=True)

    logger.info(
        f"[fusionner_colonnes_age] Colonnes '{col_age_annee}' + '{col_age_mois}' fusionnées "
        f"en '{nom_colonne_age}' ({nom_colonne_unite}) - {len(df)} lignes traitées"
    )

    return df

# ----------------------------------------------------------
# Semaines épidémiologiques
# ----------------------------------------------------------
# --- Ajouter la semaine épidémiologique à partir d’une date ---
def format_iso_week(date):
    if pd.notna(date):
        iso = date.isocalendar()
        return f"{iso.year}-S{iso.week:02d}"
    return pd.NA

def ajouter_annee_semaine_epi(
    df: pd.DataFrame,
    col_date: str | list[str],
    col_resultat: str = "Semaine_epid",
    separer_colonnes: bool = False,
    remplacer_si_existe: bool = False,
    ordre: str = "annee-semaine"  # "annee-semaine" ou "semaine-annee"
) -> pd.DataFrame:
    """
    Ajoute une colonne ISO année-semaine (ex: 2024-W15 ou W15-2024) à partir d'une ou plusieurs colonnes date.

    Args:
        df (pd.DataFrame): Le DataFrame à enrichir.
        col_date (str | list[str]): Nom(s) de colonne(s) contenant les dates.
        col_resultat (str): Nom de la colonne de sortie.
        separer_colonnes (bool): Si True, ajoute aussi Annee_epi et Num_semaine_epi.
        remplacer_si_existe (bool): Si False, ne remplace pas si col_resultat existe déjà.
        ordre (str): Format de sortie, "annee-semaine" ou "semaine-annee".

    Returns:
        pd.DataFrame: Le DataFrame avec les colonnes ajoutées.
    """

    if isinstance(col_date, str):
        if col_date not in df.columns:
            logger.warning(f"[SemaineEpi] Colonne '{col_date}' introuvable dans le DataFrame.")
            return df
        date_series = pd.to_datetime(df[col_date], errors="coerce")

    elif isinstance(col_date, list):
        colonnes_existantes = [col for col in col_date if col in df.columns]
        colonnes_manquantes = [col for col in col_date if col not in df.columns]

        for col in colonnes_manquantes:
            logger.warning(f"[SemaineEpi] Colonne '{col}' absente. Ignorée.")

        if not colonnes_existantes:
            logger.error("[SemaineEpi] Aucune des colonnes spécifiées n'existe dans le DataFrame.")
            return df

        date_series = pd.to_datetime(df[colonnes_existantes].bfill(axis=1).iloc[:, 0], errors="coerce")
    else:
        raise ValueError("col_date doit être une chaîne ou une liste de chaînes.")

    # Fonction locale pour formater selon l'ordre choisi
    def format_iso_week_custom(d):
        if pd.isna(d):
            return pd.NA
        iso = d.isocalendar()
        if ordre == "semaine-annee":
            return f"S{iso.week:02d}-{iso.year}"
        return f"{iso.year}-S{iso.week:02d}"

    # Ajouter ou non la colonne Semaine_epid
    if col_resultat in df.columns and not remplacer_si_existe:
        logger.info(f"[SemaineEpi] Colonne '{col_resultat}' déjà présente et 'remplacer_si_existe=False'. Non modifiée.")
    else:
        df[col_resultat] = date_series.apply(format_iso_week_custom)
        logger.info(f"[SemaineEpi] Colonne '{col_resultat}' ajoutée ou remplacée (ordre={ordre}).")

    if separer_colonnes:
        df["Annee_epi"] = date_series.apply(
            lambda d: d.isocalendar().year if pd.notna(d) else pd.NA
        )
        df["Num_semaine_epi"] = date_series.apply(
            lambda d: d.isocalendar().week if pd.notna(d) else pd.NA
        )
        logger.info("[SemaineEpi] Colonnes 'Annee_epi' et 'Num_semaine_epi' ajoutées.")

    return df


# ----------------------------------------------------------
# Numero epi individuel
# ----------------------------------------------------------
#  Nettoyage de valeurs aberrante de numéro Epi
def nettoyer_reference(ref):
    """
    Nettoie et normalise une référence épidémiologique :
    - Supprime NaN, None, valeurs vides, tiret seul
    - Met en majuscules
    - Remplace espaces, underscores, tirets multiples par "-"
    - Supprime les tirets au début/fin
    """
    if pd.isna(ref):
        return ""
    ref = str(ref).strip()
    if ref in ["", "-", "NAN", "NaN", "nan"]:
        return ""
    ref = ref.upper()
    ref = re.sub(r"[\s\-_]+", "-", ref)
    ref = ref.strip("-")
    ref = re.sub(r"-{2,}", "-", ref)
    return ref

def nettoyer_numero_epi(df: pd.DataFrame, cols):
    """
    Nettoie une ou plusieurs colonnes d'un DataFrame en appliquant `nettoyer_reference`.
    Cas particuliers :
    - N_epid : uniformiser les préfixes en 'RDC-'
    - N_epid_prov : enlever 'RDC-' ou 'DRC-' au début

    Args:
        df (pd.DataFrame): Le DataFrame à traiter
        cols (str ou list): Nom de la colonne ou liste de colonnes à nettoyer

    Returns:
        pd.DataFrame: DataFrame avec les colonnes nettoyées
    """
    if isinstance(cols, str):
        cols = [cols]

    colonnes_dupliquees = [col for col in cols if cols.count(col) > 1]
    colonnes_absentes = [col for col in cols if col not in df.columns]

    if colonnes_dupliquees:
        logger.info(f"Colonnes dupliquées ignorées : {sorted(set(colonnes_dupliquees))}")
    if colonnes_absentes:
        logger.warning(f"Colonnes absentes ignorées : {sorted(colonnes_absentes)}")

    for col in set(cols) - set(colonnes_absentes):
        # Nettoyage standard
        df[col] = df[col].apply(nettoyer_reference)

        if col == "N_epid":
            # Remplacer toutes les variantes par RDC-
            df[col] = df[col].astype(str).str.replace(
                r'^(RDS-|RDVC-|RDV-|DRC-|ERDC-|RDC-)',
                'RDC-',
                regex=True
            )

        elif col == "N_epid_prov":
            # Enlever RDC- ou DRC- au début
            df[col] = df[col].astype(str).str.replace(
                r'^(RDC-|DRC-)',
                '',
                regex=True
            )

    return df

# Identifiant unique pour chaque individu
def generer_code_individus(
    df: pd.DataFrame,
    colonne_date: list = ['Date_admission'],
    nom_colonne_code: str = 'Code_individu',
    database_pyramide: pd.DataFrame = None,
    colonnes_province: list = ['Province'],
    colonnes_zone: list = ['Zone_de_sante'],
    ignore_lignes_vides: bool = True,
    normaliser_colonnes: bool = True,
    afficher_erreurs_fusion: bool = True,
    export_erreurs_fusion_path: str = None,
    ignorer_lignes_non_fusionnees: bool = True,
    supprimer_colonnes_ref: bool = True,
    retourner_rapport: bool = False,
    seuil_similarite: float = 0.92,
    utiliser_matching_fluo: bool = False
) -> pd.DataFrame:
    """
    Génère un identifiant unique 'Code_individu' pour chaque ligne du DataFrame en combinant les codes pays,
    province, zone de santé, année extraite d’une date, et un compteur unique par couple province/année.

    Le code généré suit le format : 'RDC-KIN-MAT-24-001'.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame source contenant les données à coder.
    colonne_date : list of str, optionnel
        Liste des noms de colonnes candidates où chercher la date (exemple : ['Date_admission', 'Date_debut_maladie']).
    nom_colonne_code : str, optionnel
        Nom de la colonne à créer dans le DataFrame avec le code généré.
    database_pyramide : pd.DataFrame
        Table de référence contenant les colonnes : Code_Pays, Code_Province, Code_zone_de_sante, Province, Zone_de_sante.
    colonnes_province : list of str, optionnel
        Liste des colonnes candidates dans df où trouver le nom de la province.
    colonnes_zone : list of str, optionnel
        Liste des colonnes candidates dans df où trouver le nom de la zone de santé.
    ignore_lignes_vides : bool, optionnel, par défaut True
        Si True, conserve les lignes ayant des valeurs manquantes dans province, zone ou date.
        Sinon, une erreur est levée si de telles lignes existent.
    normaliser_colonnes : bool, optionnel, par défaut True
        Si True, applique un nettoyage et une normalisation (ex : suppression accents, mise en titre) sur les colonnes province et zone.
    afficher_erreurs_fusion : bool, optionnel, par défaut True
        Si True, affiche dans les logs les couples province/zone non trouvés lors de la fusion avec la base de référence.
    export_erreurs_fusion_path : str ou None, optionnel
        Chemin pour exporter au format CSV les couples province/zone non fusionnés. Ne s’active que si afficher_erreurs_fusion=True.
    ignorer_lignes_non_fusionnees : bool, optionnel, par défaut True
        Si False, lève une erreur si des lignes n’ont pas pu être fusionnées avec la base de référence.
    supprimer_colonnes_ref : bool, optionnel, par défaut True
        Si True, supprime les colonnes intermédiaires issues de la fusion avant de retourner le DataFrame.
    retourner_rapport : bool, optionnel, par défaut False
        Si True, affiche via logging un résumé du traitement à la fin.
    seuil_similarite : float, optionnel, par défaut 0.92
        Seuil de similarité (entre 0 et 1) utilisé pour le matching flou sur les noms de province/zone si activé.
    utiliser_matching_fluo : bool, optionnel, par défaut False
        Active le matching flou sur les colonnes province et zone pour corriger les erreurs typographiques lors de la fusion.

    Retour
    ------
    pd.DataFrame
        Le DataFrame enrichi avec la colonne contenant les codes uniques 'Code_individu'.

    Exemple
    -------
    >>> col_date = ['Date_admission', 'Date_debut_maladie']
    >>> col_prov = ['Province_notification', 'Province_provenance']
    >>> col_zone = ['Zone_de_sante_notification', 'Zone_de_sante_provenance']
    >>> pyramide = clean_database_pyramide()
    >>> df_codes = generer_code_individus(
    ...     df=df_export,
    ...     colonne_date=col_date,
    ...     colonnes_province=col_prov,
    ...     colonnes_zone=col_zone,
    ...     nom_colonne_code='Code_individu',
    ...     database_pyramide=pyramide,
    ...     ignore_lignes_vides=True,
    ...     normaliser_colonnes=True,
    ...     afficher_erreurs_fusion=True,
    ...     ignorer_lignes_non_fusionnees=True,
    ...     supprimer_colonnes_ref=True,
    ...     retourner_rapport=True,
    ...     utiliser_matching_fluo=True,
    ...     seuil_similarite=0.92
    ... )
    """

    if database_pyramide is None:
        logging.info(f"La base de données pyramide est utilisée")
        database_pyramide=pyramide

    df = df.copy()
    db = database_pyramide.copy()
    db.columns = db.columns.str.strip()

    colonnes_ref = ['Code_Pays', 'Code_Province', 'Code_zone_de_sante', 'Province', 'Zone_de_sante']
    rename_dict = {col: f"{col}_py" for col in colonnes_ref if col in db.columns}
    db.rename(columns=rename_dict, inplace=True)

    def priorite_valeurs(row, colonnes):
        for col in colonnes:
            if col in row:
                val = row[col]
                if pd.notnull(val) and str(val).strip() != "":
                    return val
        return None

    def nettoyer_texte(val):
        if pd.isnull(val):
            return val
        val = str(val).strip().replace("_", " ")
        val = unicodedata.normalize('NFKD', val).encode('ASCII', 'ignore').decode()
        val = val.lower().title()
        return val

    # Extraction des valeurs finales selon priorité des colonnes
    df['Province_finale'] = df.apply(lambda r: priorite_valeurs(r, colonnes_province), axis=1)
    df['Zone_finale'] = df.apply(lambda r: priorite_valeurs(r, colonnes_zone), axis=1)
    df['Date_finale'] = df.apply(lambda r: priorite_valeurs(r, colonne_date), axis=1)

    # Vérification lignes vides
    lignes_vides = df[['Province_finale', 'Zone_finale', 'Date_finale']].isnull().any(axis=1)
    nb_lignes_avant = df.shape[0]
    nb_vides = lignes_vides.sum()

    if nb_vides > 0 and not ignore_lignes_vides:
        raise ValueError(f"{nb_vides} lignes avec province/zone/date vides (option ignore_lignes_vides=False).")

    # Nettoyage texte
    if normaliser_colonnes:
        df['Province_finale'] = df['Province_finale'].apply(nettoyer_texte)
        df['Zone_finale'] = df['Zone_finale'].apply(nettoyer_texte)
        for col in ['Province_py', 'Zone_de_sante_py']:
            if col in db.columns:
                db[col] = db[col].apply(nettoyer_texte)

    # Fusion initiale
    df_merge = df.merge(
        db,
        left_on=['Province_finale', 'Zone_finale'],
        right_on=['Province_py', 'Zone_de_sante_py'],
        how='left',
        validate='m:1'
    )

    # Gestion matching flou si activé
    if utiliser_matching_fluo:
        non_fusionnees_idx = df_merge[df_merge['Code_Pays_py'].isnull()].index
        if not non_fusionnees_idx.empty:
            provinces_ref = db['Province_py'].dropna().unique()
            zones_ref = db['Zone_de_sante_py'].dropna().unique()
    
            def match_fluo(valeur, liste_ref):
                if pd.isnull(valeur):
                    return None
                match, score, _ = process.extractOne(valeur, liste_ref, scorer=fuzz.ratio)
                if (score / 100) >= seuil_similarite:
                    return match
                return None

            for idx in non_fusionnees_idx:
                prov_orig = df_merge.at[idx, 'Province_finale']
                zone_orig = df_merge.at[idx, 'Zone_finale']
                prov_corr = match_fluo(prov_orig, provinces_ref)
                zone_corr = match_fluo(zone_orig, zones_ref)
                if prov_corr:
                    df_merge.at[idx, 'Province_finale'] = prov_corr
                if zone_corr:
                    df_merge.at[idx, 'Zone_finale'] = zone_corr

            # Refusion après correction
            df_merge.drop(columns=list(rename_dict.values()), inplace=True, errors='ignore')
            df_merge = df_merge.drop(columns=['Code_Pays_py', 'Code_Province_py', 'Code_zone_de_sante_py'], errors='ignore')
            df_merge = df_merge.merge(
                db,
                left_on=['Province_finale', 'Zone_finale'],
                right_on=['Province_py', 'Zone_de_sante_py'],
                how='left',
                validate='m:1'
            )

    lignes_non_trouvees = df_merge[df_merge['Code_Pays_py'].isnull()][['Province_finale', 'Zone_finale']].drop_duplicates()
    nb_non_fusionnees = lignes_non_trouvees.shape[0]

    if nb_non_fusionnees > 0 and afficher_erreurs_fusion:
        logging.info("❌ ATTENTION : Certains couples Province / Zone introuvables dans la base de référence :")
        logging.info("\n" + lignes_non_trouvees.to_string(index=False))
        if export_erreurs_fusion_path:
            lignes_non_trouvees.to_csv(export_erreurs_fusion_path, index=False, encoding='utf-8')
            logging.info(f"💾 Export des erreurs de fusion : {export_erreurs_fusion_path}")

    if nb_non_fusionnees > 0 and not ignorer_lignes_non_fusionnees:
        raise ValueError(f"{nb_non_fusionnees} couple(s) non trouvés dans la base de référence.")

    # Traitement date + compteur unique
    df_merge['Annee'] = pd.to_datetime(df_merge['Date_finale'], errors='coerce').dt.year % 100
    nb_dates_invalides = df_merge['Annee'].isnull().sum()
    df_merge['Annee'] = df_merge['Annee'].astype('Int64')

    mask_compteur = df_merge['Code_Province_py'].notnull() & df_merge['Annee'].notnull()
    df_merge.loc[mask_compteur, 'Compteur'] = df_merge[mask_compteur].groupby(['Code_Province_py', 'Annee']).cumcount() + 1
    df_merge['Compteur_str'] = df_merge['Compteur'].apply(lambda x: f"{int(x):03d}" if pd.notnull(x) else "")

    def construire_code(row):
        if any(pd.isnull([row['Code_Pays_py'], row['Code_Province_py'], row['Code_zone_de_sante_py'], row['Annee']])) or row['Compteur_str'] == "":
            return ""
        return f"{row['Code_Pays_py']}-{row['Code_Province_py']}-{row['Code_zone_de_sante_py']}-{str(row['Annee']).zfill(2)}-{row['Compteur_str']}"

    df_merge[nom_colonne_code] = df_merge.apply(construire_code, axis=1)

    # Nettoyage colonnes intermédiaires
    colonnes_a_supprimer = [
        'Province_finale', 'Zone_finale', 'Date_finale',
        'Annee', 'Compteur', 'Compteur_str'
    ]
    if supprimer_colonnes_ref:
        colonnes_a_supprimer += [col for col in rename_dict.values() if col in df_merge.columns]

    df_merge.drop(columns=colonnes_a_supprimer, inplace=True)

    # Rapport final via logging
    if retourner_rapport:
        logging.info(f"Nombre total de lignes avant filtrage : {nb_lignes_avant}")
        logging.info(f"Nombre de lignes avec province/zone/date vides : {nb_vides}")
        logging.info(f"Nombre de lignes non fusionnées (province/zone introuvables) : {nb_non_fusionnees}")
        logging.info(f"Nombre de lignes avec date invalide : {nb_dates_invalides}")

    return df_merge
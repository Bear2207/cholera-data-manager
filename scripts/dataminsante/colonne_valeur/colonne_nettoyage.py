# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/colonne_nettoyage.py
# Notice : Pour le nettoyage de colonnes de df et son organisatison

import pandas as pd
import re
import unicodedata
import logging
from typing import Optional, Union
from pathlib import Path

# Configuration minimale du logging (modifiable globalement)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définir le chemin racine du projet à partir de ce fichier
base_dir = Path(__file__).resolve().parents[2]
mapping_file_path = base_dir / "data" / "Rename_columns.xlsx"
# Vérification de conformité des colonnes
def verifier_colonnes(df: pd.DataFrame, colonnes_attendues: list[str], afficher: str = "toutes") -> None:
    """
    Vérifie la conformité des colonnes du DataFrame par rapport à une liste de référence.
    
    Affiche :
    - les colonnes manquantes (attendues mais absentes)
    - les colonnes non attendues (présentes mais non attendues)
    
    Paramètres :
    - df : DataFrame à vérifier
    - colonnes_attendues : Liste des noms de colonnes attendues
    - afficher : "toutes" | "manquantes" | "non_attendues" | "rien"
    """
    if afficher not in {"toutes", "manquantes", "non_attendues", "rien"}:
        raise ValueError("Le paramètre 'afficher' doit être 'toutes', 'manquantes', 'non_attendues' ou 'rien'.")

    if afficher == "rien":
        return  # Ne rien afficher du tout

    colonnes_df = df.columns.tolist()
    manquantes = [col for col in colonnes_attendues if col not in colonnes_df]
    non_attendues = [col for col in colonnes_df if col not in colonnes_attendues]

    if afficher in ("toutes", "manquantes"):
        if manquantes:
            logger.warning("⚠️ Colonnes manquantes (absentes du DataFrame mais attendues) :")
            for col in manquantes:
                logger.warning(f"  - {col}")
        else:
            logger.info("✅ Aucune colonne manquante.")

    if afficher in ("toutes", "non_attendues"):
        if non_attendues:
            logger.warning("⚠️ Colonnes non attendues (présentes dans le DataFrame mais non attendues) :")
            for col in non_attendues:
                logger.warning(f"  - {col}")
        else:
            logger.info("✅ Aucune colonne inattendue.")

# Nettoyage individuel d’un nom de colonne 
def standardiser_nom(nom_col: str) -> str:
    """
    Nettoie un nom de colonne :
    - Supprime les accents
    - Minuscule + remplace tout caractère spécial/ponctuation par un underscore
    - Supprime les underscores multiples
    - Capitalise le premier mot
    """
    nom_col = unicodedata.normalize('NFKD', nom_col).encode('ASCII', 'ignore').decode('utf-8')
    nom_col = nom_col.strip().lower()
    nom_col = re.sub(r"[^\w\s]", "_", nom_col)
    nom_col = re.sub(r"\s+", "_", nom_col)
    nom_col = re.sub(r"_+", "_", nom_col)
    nom_col = nom_col.strip('_')

    mots = nom_col.split('_')
    if mots:
        mots[0] = mots[0].capitalize()
    return '_'.join(mots)


# Renommer les colonnes à partir d’un fichier de mapping Excel
def renommer_colonnes_selon_mapping(df: pd.DataFrame, mapping_file: Union[str, Path] = mapping_file_path) -> pd.DataFrame:
    """
    Renomme les colonnes selon un mapping Excel (colonnes : ancien_nom, nouveau_nom).
    """
    mapping_file = Path(mapping_file)
    if not mapping_file.exists():
        raise FileNotFoundError(f"❌ Fichier de mapping introuvable : {mapping_file}")

    mapping_df = pd.read_excel(mapping_file, dtype=str).dropna()
    if mapping_df.shape[1] < 2:
        raise ValueError("❌ Le fichier de mapping doit avoir au moins deux colonnes.")

    mapping_dict = dict(zip(mapping_df.iloc[:, 0].str.strip(), mapping_df.iloc[:, 1].str.strip()))
    mapping_utilisable = {k: v for k, v in mapping_dict.items() if k in df.columns}

    if not mapping_utilisable:
        logger.warning("⚠️ Aucun nom de colonne du mapping ne correspond à celles du DataFrame.")
        return df

    logger.info(f"✅ Colonnes renommées selon mapping : {mapping_utilisable}")
    return df.rename(columns=mapping_utilisable)


# Standardisation globale des noms de colonnes (avec ou sans mapping)
def standardiser_noms_colonnes(
    df: pd.DataFrame,
    mapping_file: Optional[Union[str, Path]] = None,
    nom_col: Optional[str] = None
) -> Union[pd.DataFrame, str]:
    """
    - Si `nom_col` est fourni : retourne sa version nettoyée.
    - Sinon : nettoie toutes les colonnes et applique un mapping si précisé.
    fonctions utilisées :
    - `standardiser_nom` pour nettoyer un nom de colonne.
    - `renommer_colonnes_selon_mapping` pour renommer selon un fichier de mapping.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("❌ L'objet passé n'est pas un DataFrame.")

    if nom_col:
        if nom_col not in df.columns:
            raise ValueError(f"❌ Colonne '{nom_col}' absente du DataFrame.")
        return standardiser_nom(nom_col)

    df.columns = [standardiser_nom(col) for col in df.columns]

    if mapping_file:
        df = renommer_colonnes_selon_mapping(df, mapping_file)

    return df

# Reclasser les colonnes
def reclasser_colonnes(
    df: pd.DataFrame,
    colonnes_prioritaires: list[str] = None,
    trier_autres: bool = False
) -> pd.DataFrame:
    """
    Reclasse les colonnes d'un DataFrame en mettant les colonnes prioritaires au début.

    Signale les doublons et colonnes absentes via le module logging.

    Args:
        df (pd.DataFrame): DataFrame d'entrée.
        colonnes_prioritaires (list[str]): Colonnes à forcer au début.
        trier_autres (bool): Si True, trie les autres colonnes alphabétiquement.

    Returns:
        pd.DataFrame: DataFrame avec colonnes reclassées.
    """
    if colonnes_prioritaires is None:
        colonnes_prioritaires = []

    colonnes_vues = set()
    colonnes_dupliquees = set()
    colonnes_absentes = []

    colonnes_prioritaires_uniques = []
    for col in colonnes_prioritaires:
        if col not in df.columns:
            colonnes_absentes.append(col)
            continue
        if col in colonnes_vues:
            colonnes_dupliquees.add(col)
        else:
            colonnes_vues.add(col)
            colonnes_prioritaires_uniques.append(col)

    if colonnes_dupliquees:
        logger.info(f"Colonnes dupliquées ignorées : {sorted(colonnes_dupliquees)}")

    if colonnes_absentes:
        logger.warning(f"Colonnes absentes ignorées : {sorted(colonnes_absentes)}")

    autres_colonnes = [col for col in df.columns if col not in colonnes_prioritaires_uniques]
    if trier_autres:
        autres_colonnes = sorted(autres_colonnes)

    nouvel_ordre = colonnes_prioritaires_uniques + autres_colonnes
    return df[nouvel_ordre]

# ------------------------------------------------
# Fonction principale à utiliser dans un pipeline
# ------------------------------------------------
def clean_all_column_names(df: pd.DataFrame) -> pd.DataFrame:
    return standardiser_noms_colonnes(df, mapping_file=mapping_file_path)

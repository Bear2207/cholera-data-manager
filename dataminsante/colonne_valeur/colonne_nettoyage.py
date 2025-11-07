# -*- coding: utf-8 -*-
"""
Module : dataminsante.colonne_valeur.colonne_nettoyage
------------------------------------------------------
Outils de nettoyage et de standardisation des noms de colonnes
dans les fichiers Excel ou CSV utilisés par le système dataminsante.

Principales fonctionnalités :
- Vérification de conformité des colonnes
- Standardisation des noms (accents, majuscules, ponctuation)
- Renommage via fichier de mapping Excel
- Reclassement des colonnes selon priorité
"""

import re
import unicodedata
import logging
from pathlib import Path
from typing import Optional, Union, List

import pandas as pd

# ------------------------------------------------------------
# Configuration du logger local
# ------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# ------------------------------------------------------------
# Constantes globales
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
MAPPING_FILE_PATH = BASE_DIR / "data" / "Rename_columns.xlsx"

__all__ = [
    "verifier_colonnes",
    "standardiser_nom",
    "renommer_colonnes_selon_mapping",
    "standardiser_noms_colonnes",
    "reclasser_colonnes",
    "clean_all_column_names",
]

# ============================================================
# 1️⃣ Vérification des colonnes
# ============================================================
def verifier_colonnes(
    df: pd.DataFrame,
    colonnes_attendues: List[str],
    afficher: str = "toutes"
) -> None:
    """
    Vérifie la conformité des colonnes du DataFrame par rapport à une liste de référence.

    Args:
        df: DataFrame à vérifier.
        colonnes_attendues: Liste des noms attendus.
        afficher: "toutes" | "manquantes" | "non_attendues" | "rien".
    """
    if afficher not in {"toutes", "manquantes", "non_attendues", "rien"}:
        raise ValueError("Le paramètre 'afficher' doit être 'toutes', 'manquantes', 'non_attendues' ou 'rien'.")

    if afficher == "rien":
        return

    colonnes_df = df.columns.tolist()
    manquantes = [c for c in colonnes_attendues if c not in colonnes_df]
    non_attendues = [c for c in colonnes_df if c not in colonnes_attendues]

    if afficher in ("toutes", "manquantes"):
        if manquantes:
            logger.warning("⚠️ Colonnes manquantes (absentes du DataFrame mais attendues) :")
            for c in manquantes:
                logger.warning(f"  - {c}")
        else:
            logger.info("✅ Aucune colonne manquante.")

    if afficher in ("toutes", "non_attendues"):
        if non_attendues:
            logger.warning("⚠️ Colonnes non attendues (présentes mais non attendues) :")
            for c in non_attendues:
                logger.warning(f"  - {c}")
        else:
            logger.info("✅ Aucune colonne inattendue.")


# ============================================================
# 2️⃣ Nettoyage individuel des noms
# ============================================================
def standardiser_nom(nom_col: str) -> str:
    """
    Standardise un nom de colonne :
    - Supprime les accents
    - Convertit en minuscules
    - Remplace ponctuation et espaces par underscore
    - Supprime les underscores multiples
    - Capitalise le premier mot

    Exemple :
        "N° Age (mois)" → "N_age_mois"
    """
    if not isinstance(nom_col, str):
        return ""

    nom_col = unicodedata.normalize("NFKD", nom_col).encode("ASCII", "ignore").decode("utf-8")
    nom_col = re.sub(r"[^\w\s]", "_", nom_col.strip().lower())
    nom_col = re.sub(r"\s+", "_", nom_col)
    nom_col = re.sub(r"_+", "_", nom_col).strip("_")

    mots = nom_col.split("_")
    if mots:
        mots[0] = mots[0].capitalize()
    return "_".join(mots)


# ============================================================
# 3️⃣ Renommage via mapping Excel
# ============================================================
def renommer_colonnes_selon_mapping(
    df: pd.DataFrame,
    mapping_file: Union[str, Path] = MAPPING_FILE_PATH
) -> pd.DataFrame:
    """
    Renomme les colonnes selon un fichier Excel de mapping.
    Le fichier doit contenir deux colonnes : ancien_nom, nouveau_nom.
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


# ============================================================
# 4️⃣ Standardisation globale
# ============================================================
def standardiser_noms_colonnes(
    df: pd.DataFrame,
    mapping_file: Optional[Union[str, Path]] = None,
    nom_col: Optional[str] = None
) -> Union[pd.DataFrame, str]:
    """
    Standardise toutes les colonnes ou un nom spécifique.

    - Si `nom_col` est fourni : retourne la version nettoyée.
    - Sinon : nettoie tout le DataFrame et applique un mapping si disponible.
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


# ============================================================
# 5️⃣ Reclassement des colonnes
# ============================================================
def reclasser_colonnes(
    df: pd.DataFrame,
    colonnes_prioritaires: Optional[List[str]] = None,
    trier_autres: bool = False
) -> pd.DataFrame:
    """
    Replace les colonnes prioritaires au début du DataFrame,
    avec option de tri des autres colonnes.

    Args:
        colonnes_prioritaires: Colonnes à placer en premier.
        trier_autres: Si True, trie les autres colonnes alphabétiquement.
    """
    colonnes_prioritaires = colonnes_prioritaires or []

    absentes = [c for c in colonnes_prioritaires if c not in df.columns]
    if absentes:
        logger.warning(f"Colonnes absentes ignorées : {absentes}")

    prioritaires = [c for c in colonnes_prioritaires if c in df.columns]
    autres = [c for c in df.columns if c not in prioritaires]
    if trier_autres:
        autres = sorted(autres)

    return df[prioritaires + autres]


# ============================================================
# 6️⃣ Fonction principale pipeline
# ============================================================
def clean_all_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et standardise toutes les colonnes du DataFrame
    selon la logique définie dans ce module et le fichier de mapping.
    """
    return standardiser_noms_colonnes(df, mapping_file=MAPPING_FILE_PATH)


# ============================================================
# 7️⃣ Test rapide du module
# ============================================================
if __name__ == "__main__":
    # Exemple minimal de test
    data = {"Âge (ans)": [12, 34], "Nom du Patient": ["Alice", "Bob"], "Sexe": ["F", "M"]}
    df = pd.DataFrame(data)
    print("Avant :", df.columns.tolist())
    df_clean = clean_all_column_names(df)
    print("Après :", df_clean.columns.tolist())

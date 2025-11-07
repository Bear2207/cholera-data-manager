# -*- coding: utf-8 -*-
"""
Module : dataminsante.compilation.fichiers_compilation
------------------------------------------------------
Gère la compilation, la standardisation et la fusion des fichiers Excel
de surveillance épidémiologique (Rougeole, Choléra, etc.).

Fonctionnalités principales :
- Recherche récursive des fichiers Excel correspondant à un motif.
- Lecture et standardisation des noms de colonnes.
- Détection et correction des doublons de colonnes.
- Fusion intelligente de fichiers et feuilles.
- Gestion des logs et exportation automatique horodatée.
"""

from __future__ import annotations

import os
import fnmatch
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict, Tuple
from collections import defaultdict

import pandas as pd

# Import explicite des outils de nettoyage
from dataminsante.colonne_valeur.colonne_nettoyage import (
    standardiser_nom,
    clean_all_column_names,
    verifier_colonnes,
)

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
    "lister_fichiers_excel",
    "lire_fichiers_excel",
    "detecter_doublons_standardises",
    "rendre_colonnes_uniques",
    "renommer_colonnes_avec_provenance",
    "afficher_colonnes_standardisees",
    "fusionner_colonnes_similaires",
    "comparer_colonnes_multiples",
    "charger_fichiers_excel",
    "exporter_dataframe_excel",
    "fusionner_fichiers_homogenes",
    "charger_fichiers_excel_avec_log",
]


# ============================================================
# 1️⃣ Fonctions utilitaires
# ============================================================
def lister_fichiers_excel(
    dossier_racine: Union[str, Path],
    motif_fichier: str = "*LL_Rougeole.xlsx",
    sensible_a_la_casse: bool = False
) -> List[Path]:
    """
    Liste les fichiers Excel valides dans un dossier donné (récursif).

    Args:
        dossier_racine: Dossier racine à parcourir.
        motif_fichier: Motif à rechercher (ex: "*LL_Cholera.xlsx").
        sensible_a_la_casse: Respecter la casse du motif.

    Returns:
        Liste de chemins vers les fichiers trouvés.
    """
    dossier = Path(dossier_racine)
    if not dossier.exists():
        raise ValueError(f"Dossier inexistant : {dossier_racine}")

    fichiers_trouves = []
    for fichier in dossier.rglob("*.xlsx"):
        if fichier.name.startswith("~$"):
            continue

        nom = fichier.name if sensible_a_la_casse else fichier.name.lower()
        motif = motif_fichier if sensible_a_la_casse else motif_fichier.lower()

        if fnmatch.fnmatch(nom, motif):
            fichiers_trouves.append(fichier)

    logger.info(
        f"{len(fichiers_trouves)} fichiers trouvés avec motif '{motif_fichier}' dans {dossier_racine}."
    )
    return fichiers_trouves


def lire_fichiers_excel(
    liste_fichiers: List[Path],
    sheet_name: str = "Feuille1",
    sensible_a_la_casse: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Lit une liste de fichiers Excel et retourne un dictionnaire de DataFrames.

    Args:
        liste_fichiers: Liste des chemins des fichiers à lire.
        sheet_name: Nom de la feuille cible.
        sensible_a_la_casse: Si True, recherche sensible à la casse.

    Returns:
        dict: {nom_fichier: DataFrame}
    """
    donnees = {}
    for chemin in liste_fichiers:
        nom_fichier = os.path.basename(chemin)
        try:
            xl = pd.ExcelFile(chemin)
            feuilles = xl.sheet_names
            feuille_choisie = None

            if sensible_a_la_casse:
                if sheet_name in feuilles:
                    feuille_choisie = sheet_name
            else:
                feuilles_lower = [f.lower() for f in feuilles]
                if sheet_name.lower() in feuilles_lower:
                    feuille_choisie = feuilles[feuilles_lower.index(sheet_name.lower())]

            if not feuille_choisie:
                raise ValueError(f"Feuille '{sheet_name}' non trouvée dans {nom_fichier}")

            df = xl.parse(sheet_name=feuille_choisie)
            donnees[nom_fichier] = df
            logger.info(f"✅ Lu : {nom_fichier} - feuille : {feuille_choisie}")

        except Exception as e:
            logger.warning(f"❌ Erreur de lecture {nom_fichier} : {e}")
    return donnees


def detecter_doublons_standardises(df: pd.DataFrame, provenance: str) -> List[str]:
    """Détecte les doublons après standardisation des noms de colonnes."""
    noms_std = [standardiser_nom(c) for c in df.columns]
    compteur = defaultdict(int)
    for nom in noms_std:
        compteur[nom] += 1
    doublons = [n for n, c in compteur.items() if c > 1]
    if doublons:
        logger.warning(f"[{provenance}] Colonnes standardisées en doublon : {doublons}")
    return doublons


def rendre_colonnes_uniques(cols: List[str]) -> List[str]:
    """Rend les noms de colonnes uniques (_01, _02...)."""
    compteur = defaultdict(int)
    uniques = []
    for c in cols:
        compteur[c] += 1
        uniques.append(f"{c}_{compteur[c]-1:02d}" if compteur[c] > 1 else c)
    return uniques


# ============================================================
# 2️⃣ Fonctions de traitement / transformation
# ============================================================
def renommer_colonnes_avec_provenance(
    df: pd.DataFrame,
    provenance: str,
    colonnes_a_renommer: Optional[List[str]] = None
) -> pd.DataFrame:
    """Renomme les colonnes d’un DataFrame en ajoutant la provenance comme suffixe."""
    if colonnes_a_renommer is None:
        colonnes_a_renommer = [c for c in df.columns if c != "Provenance"]
    mapping = {c: f"{c}_{provenance}" for c in colonnes_a_renommer}
    return df.rename(columns=mapping)


def afficher_colonnes_standardisees(dataframes: List[pd.DataFrame]) -> None:
    """Affiche dans les logs les colonnes standardisées de chaque DataFrame."""
    logger.info("Affichage des colonnes standardisées :")
    for i, df in enumerate(dataframes):
        provenance = df.get("Provenance", [f"Fichier_{i+1}"])[0]
        cols_std = [standardiser_nom(c) for c in df.columns]
        logger.info(f"{provenance} : {cols_std}")


def fusionner_colonnes_similaires(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Fusionne les colonnes similaires en un seul DataFrame.
    Gère la standardisation et les suffixes.
    """
    dfs_renommes = []
    for df in dataframes:
        provenance = df.get("Provenance", ["inconnu"])[0]
        noms_std = [standardiser_nom(c) for c in df.columns]
        uniques = rendre_colonnes_uniques(noms_std)
        col_map = dict(zip(df.columns, uniques))
        df = df.rename(columns=col_map)

        doublons = df.columns[df.columns.duplicated()].tolist()
        if doublons:
            raise ValueError(f"Colonnes dupliquées dans {provenance}: {doublons}")
        dfs_renommes.append(df)

    df_final = pd.concat(dfs_renommes, ignore_index=True)

    # Fusion des colonnes suffixées (_01, _02...)
    groupes = {}
    for c in df_final.columns:
        if "_" in c and c.split("_")[-1].isdigit():
            base = "_".join(c.split("_")[:-1])
            groupes.setdefault(base, []).append(c)

    for base, cols in groupes.items():
        if base not in df_final.columns:
            df_final[base] = None
        for c in cols:
            df_final[base] = df_final[base].fillna(df_final[c])
        df_final.drop(columns=cols, inplace=True)

    # Nettoyage
    vides = [c for c in df_final.columns if c.startswith("Unnamed") and df_final[c].isnull().all()]
    if vides:
        df_final.drop(columns=vides, inplace=True)
    df_final.dropna(how="all", inplace=True)
    return df_final


def comparer_colonnes_multiples(
    dfs: Dict[str, pd.DataFrame],
    valeur_absente: str = "-"
) -> pd.DataFrame:
    """Compare les colonnes entre plusieurs DataFrames."""
    toutes_colonnes = sorted({col for df in dfs.values() for col in df.columns})
    tableau = []
    for col in toutes_colonnes:
        ligne = {"Colonne": col}
        for nom_df, df in dfs.items():
            ligne[nom_df] = col if col in df.columns else valeur_absente
        tableau.append(ligne)
    return pd.DataFrame(tableau)


# ============================================================
# 3️⃣ Fonctions principales d’orchestration
# ============================================================
def charger_fichiers_excel(
    dossier_racine: Optional[str] = None,
    liste_fichiers: Optional[List[str]] = None,
    motif_fichier: str = "*LL_Rougeole.xlsx",
    sheet_name: str = "LL_Rougeole",
    colonnes_attendues: Optional[List[str]] = None,
    sensible_a_la_casse: bool = False,
    colonne_source: Optional[str] = "Provenance"
) -> pd.DataFrame:
    """
    Charge plusieurs fichiers Excel, nettoie les colonnes,
    ajoute la colonne de provenance et fusionne le tout.
    """
    if liste_fichiers is None:
        if dossier_racine is None:
            raise ValueError("Fournir un dossier_racine ou une liste_fichiers.")
        liste_fichiers = lister_fichiers_excel(dossier_racine, motif_fichier, sensible_a_la_casse)

    fichiers = lire_fichiers_excel(liste_fichiers, sheet_name, sensible_a_la_casse)
    dataframes = []

    for fichier, df in fichiers.items():
        try:
            provenance = os.path.splitext(fichier)[0]
            df = clean_all_column_names(df)
            if colonne_source:
                df[colonne_source] = provenance
            detecter_doublons_standardises(df, provenance)
            dataframes.append(df)
        except Exception as e:
            logger.warning(f"Erreur lors du traitement {fichier} : {e}")

    if not dataframes:
        raise ValueError("Aucun fichier valide n’a été chargé.")

    afficher_colonnes_standardisees(dataframes)
    df_fusionne = fusionner_colonnes_similaires(dataframes)

    if colonnes_attendues:
        verifier_colonnes(df_fusionne, [standardiser_nom(c) for c in colonnes_attendues])

    return df_fusionne


def exporter_dataframe_excel(
    df: pd.DataFrame,
    dossier: str,
    base_nom: str,
    sheet_name: str = "Feuille1"
) -> str:
    """Exporte un DataFrame en fichier Excel horodaté."""
    os.makedirs(dossier, exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    chemin = Path(dossier) / f"{base_nom}_{horodatage}.xlsx"
    df.to_excel(chemin, index=False, sheet_name=sheet_name)
    logger.info(f"Fichier exporté : {chemin}")
    return str(chemin)


# ============================================================
# 4️⃣ Section de test rapide
# ============================================================
if __name__ == "__main__":
    dossier_test = "data/Cholera"
    try:
        fichiers = lister_fichiers_excel(dossier_test, motif_fichier="*LL_Cholera.xlsx")
        donnees = lire_fichiers_excel(fichiers, sheet_name="LL_Cholera")
        logger.info(f"{len(donnees)} fichiers lus avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du test : {e}")

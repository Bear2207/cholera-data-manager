# -*- coding: utf-8 -*-
# dataminsante/valeurs_comparaison.py

# Notice : Des fonctions rapides pour comparer des valeurs des colonnes du df

import pandas as pd
import re
import logging
from typing import List, Dict, Union
from rapidfuzz import fuzz, process

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Comparaison des colonnes ---
def comparer_colonnes_generique(
    df1: pd.DataFrame,
    colonnes_df1: Union[str, List[str]],
    df2: pd.DataFrame,
    colonnes_df2: Union[str, List[str]],
    verbose: bool = True,
    nettoyer: bool = True,
    seuil_similarite: float = 1.0  # 1.0 = égalité stricte
) -> Dict[str, List]:
    """
    Compare des colonnes (ou clés composites) entre deux DataFrames,
    avec nettoyage optionnel.
    Ajout d’un seuil de similarité pour comparaison si seuil < 1.

    Args:
        df1 (pd.DataFrame): Premier DataFrame.
        colonnes_df1 (str ou List[str]): Colonnes à comparer dans df1.
        df2 (pd.DataFrame): Deuxième DataFrame.
        colonnes_df2 (str ou List[str]): Colonnes à comparer dans df2.
        verbose (bool): Active les logs.
        nettoyer (bool): Appliquer nettoyage ou comparer "brut".
        seuil_similarite (float): Seuil de similarité [0-1]. 1 = égalité stricte.

    Returns:
        Dict[str, List]: Dictionnaire avec clés :
            - 'commun' : valeurs ou tuples communs (fuzzy si seuil < 1)
            - 'uniquement_dans_df1' : présents uniquement dans df1
            - 'uniquement_dans_df2' : présents uniquement dans df2
    """

    def nettoyer_texte(valeur):
        if pd.isnull(valeur):
            return None
        return re.sub(r"[-_\s]+", "", str(valeur)).upper()

    # Uniformiser en liste
    if isinstance(colonnes_df1, str):
        colonnes_df1 = [colonnes_df1]
    if isinstance(colonnes_df2, str):
        colonnes_df2 = [colonnes_df2]

    if verbose:
        mode = "nettoyé" if nettoyer else "brut"
        logger.info(f"Traitement {mode} des colonnes {colonnes_df1} du premier DataFrame...")

    def preparer_valeur(row, colonnes):
        valeurs = tuple(row[col] for col in colonnes)
        if nettoyer:
            nettoyes = tuple(nettoyer_texte(v) for v in valeurs)
            if None in nettoyes:
                return None
            return nettoyes if len(nettoyes) > 1 else nettoyes[0]
        else:
            if None in valeurs:
                return None
            return valeurs if len(valeurs) > 1 else valeurs[0]

    # Préparer sets si seuil == 1 (égalité stricte)
    if seuil_similarite == 1.0:
        set1 = set(
            val for val in (
                preparer_valeur(row, colonnes_df1)
                for _, row in df1.dropna(subset=colonnes_df1).iterrows()
            ) if val is not None
        )

        if verbose:
            logger.info(f"Traitement {mode} des colonnes {colonnes_df2} du deuxième DataFrame...")

        set2 = set(
            val for val in (
                preparer_valeur(row, colonnes_df2)
                for _, row in df2.dropna(subset=colonnes_df2).iterrows()
            ) if val is not None
        )

        if verbose:
            logger.info(f"Comparaison stricte des valeurs entre {colonnes_df1} et {colonnes_df2}...")

        commun = set1 & set2
        uniquement_dans_df1 = set1 - set2
        uniquement_dans_df2 = set2 - set1

        if verbose:
            logger.info(f"Valeurs communes : {len(commun)}")
            logger.info(f"Uniquement dans le premier DataFrame : {len(uniquement_dans_df1)}")
            logger.info(f"Uniquement dans le deuxième DataFrame : {len(uniquement_dans_df2)}")

        return {
            "Valeurs communes ": sorted(commun),
            "Uniquement dans le premier DataFrame ": sorted(uniquement_dans_df1),
            "Uniquement dans le deuxième DataFrame": sorted(uniquement_dans_df2),
        }

    # Sinon, fuzzy matching avec rapidfuzz
    else:
        from rapidfuzz import fuzz, process

        seuil_100 = int(seuil_similarite * 100)

        valeurs_df2 = {
            preparer_valeur(row, colonnes_df2)
            for _, row in df2.dropna(subset=colonnes_df2).iterrows()
            if preparer_valeur(row, colonnes_df2) is not None
        }

        if verbose:
            logger.info(f"Recherche fuzzy sur {len(valeurs_df2)} valeurs dans df2 avec seuil {seuil_similarite}")

        commun = []
        uniquement_dans_df1 = []

        for _, row in df1.dropna(subset=colonnes_df1).iterrows():
            val1 = preparer_valeur(row, colonnes_df1)
            if val1 is None:
                continue
            resultat = process.extractOne(
                val1, valeurs_df2, scorer=fuzz.ratio, score_cutoff=seuil_100
            )
            if resultat is None:
                uniquement_dans_df1.append(val1)
            else:
                val2, score, _ = resultat
                commun.append(val1)

        # Trouver uniquement_dans_df2 (valeurs de df2 sans match dans df1)
        valeurs_df1 = {
            preparer_valeur(row, colonnes_df1)
            for _, row in df1.dropna(subset=colonnes_df1).iterrows()
            if preparer_valeur(row, colonnes_df1) is not None
        }

        uniquement_dans_df2 = [
            val2 for val2 in valeurs_df2
            if all(
                fuzz.ratio(val2, val1) < seuil_100
                for val1 in valeurs_df1
            )
        ]

        if verbose:
            logger.info(f"Valeurs communes fuzzy : {len(commun)}")
            logger.info(f"Uniquement dans df1 (fuzzy) : {len(uniquement_dans_df1)}")
            logger.info(f"Uniquement dans df2 (fuzzy) : {len(uniquement_dans_df2)}")

        return {
            "commun": sorted(commun),
            "uniquement_dans_df1": sorted(uniquement_dans_df1),
            "uniquement_dans_df2": sorted(uniquement_dans_df2),
        }
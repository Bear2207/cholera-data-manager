# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/colonne_suppression.py

# Notice : Pour la suppression des colonnes de df

import pandas as pd
import logging
from typing import List, Optional


# Configuration du logger par défaut
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Supprimer les colonnes inutiles
def supprimer_colonnes_inutiles(
    df: pd.DataFrame,
    colonnes_a_supprimer: Optional[List[str]] = None,
    suffixe_a_supprimer: Optional[str] = None,
    colonnes_a_garder: Optional[List[str]] = None,
    garder_vides_si_gardees: bool = True
) -> pd.DataFrame:
    """
    Nettoie un DataFrame en supprimant :
    - les colonnes vides (toutes NaN), sauf si elles sont dans `colonnes_a_garder` et `garder_vides_si_gardees=True`
    - les colonnes inutiles données en paramètre
    - les colonnes non incluses dans `colonnes_a_garder` si spécifié
    - les lignes entièrement vides
    Puis, si `suffixe_a_supprimer` est renseigné, renomme les colonnes
    en supprimant ce suffixe.

    Args:
        df (pd.DataFrame): DataFrame à traiter.
        colonnes_a_supprimer (List[str], optionnel): colonnes à supprimer en plus.
        suffixe_a_supprimer (str, optionnel): suffixe à retirer des noms de colonnes.
        colonnes_a_garder (List[str], optionnel): si renseigné, seules ces colonnes seront conservées.
        garder_vides_si_gardees (bool): si True, garde les colonnes vides si elles sont dans `colonnes_a_garder`.

    Returns:
        pd.DataFrame: DataFrame nettoyé et colonnes renommées.
    """
    df = df.copy()

    # Colonnes 'Unnamed' entièrement vides
    colonnes_unnamed_vides = [
        col for col in df.columns if col.startswith("Unnamed") and df[col].isnull().all()
    ]

    # Colonnes entièrement vides
    colonnes_vides = df.columns[df.isnull().all()].tolist()

    # Gestion des colonnes vides gardées
    colonnes_vides_gardees = []
    if colonnes_a_garder and garder_vides_si_gardees:
        colonnes_vides_gardees = [col for col in colonnes_vides if col in colonnes_a_garder]
        colonnes_vides = [col for col in colonnes_vides if col not in colonnes_vides_gardees]

    # Fusion sans doublons
    colonnes_vides_toutes = list(set(colonnes_unnamed_vides + colonnes_vides))

    # Colonnes à supprimer explicitement
    colonnes_a_supprimer_finales = colonnes_vides_toutes.copy()
    if colonnes_a_supprimer:
        colonnes_existantes = [col for col in colonnes_a_supprimer if col in df.columns]
        colonnes_a_supprimer_finales.extend(colonnes_existantes)
        colonnes_a_supprimer_finales = list(set(colonnes_a_supprimer_finales))

    # Suppression des colonnes
    if colonnes_a_supprimer_finales:
        df.drop(columns=colonnes_a_supprimer_finales, inplace=True)
        logger.info(f"Colonnes supprimées : {colonnes_a_supprimer_finales}")
    else:
        logger.info("Aucune colonne supprimée.")

    # Log spécial pour colonnes vides gardées
    if colonnes_vides_gardees:
        logger.info(f"Colonnes vides mais gardées (car dans colonnes_a_garder) : {colonnes_vides_gardees}")

    # Si colonnes_a_garder est renseigné → on garde uniquement celles-ci
    if colonnes_a_garder:
        colonnes_gardees = [col for col in colonnes_a_garder if col in df.columns]
        df = df[colonnes_gardees]
        logger.info(f"Colonnes gardées : {colonnes_gardees}")

    # Suppression des lignes entièrement vides
    lignes_avant = df.shape[0]
    df.dropna(how='all', inplace=True)
    lignes_supprimees = lignes_avant - df.shape[0]

    if lignes_supprimees > 0:
        logger.info(f"{lignes_supprimees} ligne(s) entièrement vide(s) supprimée(s).")
    else:
        logger.info("Aucune ligne vide supprimée.")

    # Suppression de suffixes dans les noms de colonnes
    if suffixe_a_supprimer:
        nouvelles_colonnes = {
            col: col.removesuffix(suffixe_a_supprimer)
            for col in df.columns if col.endswith(suffixe_a_supprimer)
        }
        if nouvelles_colonnes:
            df.rename(columns=nouvelles_colonnes, inplace=True)
            logger.info(f"Suffixe '{suffixe_a_supprimer}' supprimé des colonnes : {list(nouvelles_colonnes.keys())}")
        else:
            logger.info(f"Aucun suffixe '{suffixe_a_supprimer}' trouvé dans les noms de colonnes.")

    return df

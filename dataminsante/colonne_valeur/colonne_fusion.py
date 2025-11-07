# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/colonne_fusion.py

# Notice : Pour la fusion des colonnes de df

import pandas as pd
import logging
from Levenshtein import ratio
from dataminsante.colonne_valeur.colonne_nettoyage import verifier_colonnes
import os
from typing import List, Union

logger = logging.getLogger(__name__)

def fusionner_fichiers_par_jointure(
    fichiers: List[Union[str, pd.DataFrame]],
    on: Union[str, List[str]] = None,
    how: str = "inner",
    suffixes: tuple = ("_gauche", "_droite"),
    avec_source: bool = False
) -> pd.DataFrame:
    """
    Fusionne plusieurs fichiers (ou DataFrames) par jointure sur une ou plusieurs colonnes.

    Args:
        fichiers (List[Union[str, pd.DataFrame]]): Liste de chemins ou de DataFrames.
        on (str or List[str]): Nom(s) des colonnes sur lesquelles faire la jointure.
        how (str): Type de jointure : "inner", "outer", "left", "right".
        suffixes (tuple): Suffixes pour les colonnes dupliquées.
        avec_source (bool): Ajouter une colonne de provenance pour chaque DataFrame (utile pour debug).

    Returns:
        pd.DataFrame: Résultat de la jointure progressive.
    """

    if not fichiers or len(fichiers) < 2:
        raise ValueError("Il faut au moins deux fichiers pour une jointure.")

    def charger_fichier(fichier, index):
        if isinstance(fichier, pd.DataFrame):
            df = fichier.copy()
        elif isinstance(fichier, str):
            if not os.path.exists(fichier):
                raise FileNotFoundError(f"Fichier introuvable : {fichier}")
            ext = os.path.splitext(fichier)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(fichier)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(fichier)
            else:
                raise ValueError(f"Format non supporté : {fichier}")
        else:
            raise TypeError(f"Type non supporté : {type(fichier)}")

        if avec_source:
            df["Source"] = f"df_{index}"

        return df

    # Charger les fichiers
    df_liste = []
    for i, f in enumerate(fichiers):
        try:
            df_liste.append(charger_fichier(f, i))
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier {i}: {e}")
            continue

    if len(df_liste) < 2:
        raise ValueError("Moins de deux fichiers valides chargés pour fusion.")

    # Faire la jointure progressive
    df_final = df_liste[0]
    for i in range(1, len(df_liste)):
        logger.info(f"[Jointure] df_0 avec df_{i} sur {on}, type={how}")
        try:
            df_final = df_final.merge(
                df_liste[i],
                on=on,
                how=how,
                suffixes=suffixes
            )
        except Exception as e:
            logger.error(f"Erreur lors de la jointure avec df_{i} : {e}")
            raise

    logger.info(f"[Fusion réussie] {len(df_liste)} fichiers fusionnés par jointure.")
    return df_final


# Configuration minimale du logging (modifiable globalement)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

        
# Fusionner les colonnes 
def fusionner_ligne(
    df_cols: pd.DataFrame,
    type_fusion: str = "concat",
    separateur: str = " "
) -> pd.Series:
    if type_fusion == "concat":
        return df_cols.apply(
            lambda row: separateur.join(
                str(val).strip() for val in row if pd.notna(val) and str(val).strip() != ""
            ),
            axis=1
        )
    elif type_fusion == "first_non_null":
        return df_cols.apply(
            lambda row: next(
                (val for val in row if pd.notna(val) and str(val).strip() != ""), 
                None
            ),
            axis=1
        )
    else:
        raise ValueError("type_fusion doit être 'concat' ou 'first_non_null'")

# Fonction générique pour fusionner des colonnes similaires ou des groupes de colonnes
def fusionner_colonnes_similaires_ou_groupes(
    df: pd.DataFrame,
    method: str = "similarity",
    groupes_colonnes: dict = None,
    type_fusion: str = "concat",
    seuil_similarite: float = 0.9,
    separateur: str = ' ',
    drop: bool = True
) -> pd.DataFrame:
    """
    Fonction générique pour fusionner des colonnes :
    - Soit en utilisant des groupes définis manuellement ("manual")
    - Soit en détectant les colonnes similaires automatiquement ("similarity")

    Args:
        df (pd.DataFrame): Le DataFrame d'entrée.
        method (str): Méthode pour identifier les colonnes à fusionner :
            - "manual" : utiliser un dictionnaire explicite via `groupes_colonnes`
            - "similarity" : détecter automatiquement les colonnes similaires
        groupes_colonnes (dict, optional): Dictionnaire de regroupement si method="manual".
            Exemple:
                colonnes_age = ['Age', 'Âge', 'age_en_annees']
                colonnes_identite = ['Nom', 'Prenom', 'Nom complet']
                colonnes_sexe = ['Sexe', 'Genre']
                groupes_colonnes = {
                    'age': colonnes_age,
                    'identite': colonnes_identite,
                    'sexe': colonnes_sexe
                }
        type_fusion (str): Type de fusion à appliquer :
            - "concat" : concatène les valeurs ligne par ligne
            - "first_non_null" : prend la première valeur non vide
        seuil_similarite (float): Seuil de similarité pour mode "similarity".
        separateur (str): Séparateur utilisé pour concaténation si "concat".
        drop (bool): Supprimer les colonnes fusionnées après fusion.

    Returns:
        pd.DataFrame: DataFrame avec colonnes fusionnées.
    """
    # --- Corps de la fonction ici ---

    df_result = df.copy()

    if method == "similarity":
        colonnes = list(df_result.columns)
        deja_vus = set()
        groupes = []

        for i, col1 in enumerate(colonnes):
            if col1 in deja_vus:
                continue
            groupe = [col1]
            for col2 in colonnes[i + 1:]:
                if col2 not in deja_vus and ratio(col1.lower(), col2.lower()) >= seuil_similarite:
                    groupe.append(col2)
            if len(groupe) > 1:
                groupes.append(groupe)
                deja_vus.update(groupe)

        for groupe in groupes:
            nom_col_fusion = groupe[0] + "_fusion"
            df_result[nom_col_fusion] = fusionner_ligne(df_result[groupe], type_fusion, separateur)
            logger.warning(f"[Fusion - similarity] {groupe} => {nom_col_fusion}")
            if drop:
                df_result.drop(columns=groupe, inplace=True)

    elif method == "manual":
        if not groupes_colonnes:
            raise ValueError("Le paramètre groupes_colonnes est requis pour le mode 'manual'.")

        for nom_fusion, colonnes in groupes_colonnes.items():
            # Vérification explicite des colonnes
            verifier_colonnes(df_result, colonnes,afficher="manquantes")

            nom_col_fusion = nom_fusion + "_fusion"
            colonnes_valides = [col for col in colonnes if col in df_result.columns]

            if len(colonnes_valides) < 2:
                logger.warning(f"[Fusion ignorée] Moins de 2 colonnes valides pour '{nom_fusion}'")
                continue

            df_result[nom_col_fusion] = fusionner_ligne(
                df_result[colonnes_valides], type_fusion, separateur
            )
            logger.warning(f"[Fusion - manual] {colonnes_valides} => {nom_col_fusion}")

            if drop:
                df_result.drop(columns=colonnes_valides, inplace=True)

    else:
        raise ValueError("method doit être 'similarity' ou 'manual'.")

    # Supprimer suffixe '_fusion' des colonnes fusionnées pour nettoyage final
    colonnes_fusion = [col for col in df_result.columns if col.endswith("_fusion")]
    if colonnes_fusion:
        renommage = {col: col[:-7] for col in colonnes_fusion}  # len("_fusion") == 7
        df_result.rename(columns=renommage, inplace=True)
        logger.info(f"[Renommage] Colonnes fusionnées renommées : {renommage}")

    return df_result


def fusionner_fichiers_par_jointure(
    fichiers: List[Union[str, pd.DataFrame]],
    on: Union[str, List[str]] = None,
    how: str = "inner",
    suffixes: tuple = ("_gauche", "_droite"),
    avec_source: bool = False
) -> pd.DataFrame:
    """
    Fusionne plusieurs fichiers (ou DataFrames) par jointure sur une ou plusieurs colonnes.

    Args:
        fichiers (List[Union[str, pd.DataFrame]]): Liste de chemins ou de DataFrames.
        on (str or List[str]): Nom(s) des colonnes sur lesquelles faire la jointure.
        how (str): Type de jointure : "inner", "outer", "left", "right".
        suffixes (tuple): Suffixes pour les colonnes dupliquées.
        avec_source (bool): Ajouter une colonne de provenance pour chaque DataFrame (utile pour debug).

    Returns:
        pd.DataFrame: Résultat de la jointure progressive.
    """

    if not fichiers or len(fichiers) < 2:
        raise ValueError("Il faut au moins deux fichiers pour une jointure.")

    def charger_fichier(fichier, index):
        if isinstance(fichier, pd.DataFrame):
            df = fichier.copy()
        elif isinstance(fichier, str):
            if not os.path.exists(fichier):
                raise FileNotFoundError(f"Fichier introuvable : {fichier}")
            ext = os.path.splitext(fichier)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(fichier)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(fichier)
            else:
                raise ValueError(f"Format non supporté : {fichier}")
        else:
            raise TypeError(f"Type non supporté : {type(fichier)}")

        if avec_source:
            df["Source"] = f"df_{index}"

        return df

    # Charger les fichiers
    df_liste = []
    for i, f in enumerate(fichiers):
        try:
            df_liste.append(charger_fichier(f, i))
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier {i}: {e}")
            continue

    if len(df_liste) < 2:
        raise ValueError("Moins de deux fichiers valides chargés pour fusion.")

    # Faire la jointure progressive
    df_final = df_liste[0]
    for i in range(1, len(df_liste)):
        logger.info(f"[Jointure] df_0 avec df_{i} sur {on}, type={how}")
        try:
            df_final = df_final.merge(
                df_liste[i],
                on=on,
                how=how,
                suffixes=suffixes
            )
        except Exception as e:
            logger.error(f"Erreur lors de la jointure avec df_{i} : {e}")
            raise

    logger.info(f"[Fusion réussie] {len(df_liste)} fichiers fusionnés par jointure.")
    return df_final

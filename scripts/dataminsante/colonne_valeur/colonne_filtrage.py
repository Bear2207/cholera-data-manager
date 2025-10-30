
# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/colonne_filtrage.py
# Notice : Des fonctions pour filtrer des DataFrames selon des conditions spécifiques

import pandas as pd
import logging
from typing import Optional, Union,List
from dataminsante.colonne_valeur.valeurs_nettoyage import get_target_columns

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#  Filter df
def filtrer_df(
    df: pd.DataFrame,
    condition: Optional[Union[pd.Series, list, tuple]] = None,
    colonnes: Optional[list[str]] = None
) -> pd.DataFrame:
    """
    Filtre un DataFrame selon une condition et/ou une liste de colonnes.

    Args:
        df (pd.DataFrame): DataFrame à filtrer.
        condition (pd.Series ou liste/tuple booléens, optionnel): Condition(s) de filtre.
            Peut être une Series booléenne, une liste ou un tuple de booléens, ou None.
            Si None, pas de filtrage sur les lignes.
        colonnes (list[str], optionnel): Liste des colonnes à sélectionner.
            Si None, conserve toutes les colonnes.

    Returns:
        pd.DataFrame: DataFrame filtré.
    """
    df_filtre = df

    # Appliquer condition sur les lignes
    if condition is not None:
        if isinstance(condition, (list, tuple)):
            condition = pd.Series(condition, index=df.index)
        df_filtre = df_filtre.loc[condition]

    # Sélection colonnes
    if colonnes is not None:
        colonnes_existantes = [col for col in colonnes if col in df_filtre.columns]
        df_filtre = df_filtre.loc[:, colonnes_existantes]

    return df_filtre

# --- Filtrer les lignes selon la première date non vide dans une liste de colonnes ---
def filtrer_par_premiere_date(
    df: pd.DataFrame, 
    colonnes_date: List[str], 
    annee: int, 
    garder_colonne: Union[bool, str] = False
) -> pd.DataFrame:
    """
    Filtre les lignes du DataFrame selon la première date non vide (NaT) dans une liste de colonnes datetime.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les colonnes de dates.
        colonnes_date (List[str]): Liste de colonnes à tester dans l'ordre de priorité.
        annee (int): L'année à filtrer (ex: 2025).
        garder_colonne (bool|str, optionnel): 
            - False (défaut) : supprime la colonne 'Premiere_date'.
            - True : garde la colonne 'Premiere_date'.
            - str : garde la colonne et la renomme avec ce nom.

    Returns:
        pd.DataFrame: DataFrame filtré où la première date non nulle est de l'année spécifiée.
    """
    df_copy = df.copy()

    colonnes_existantes = []
    for col in colonnes_date:
        if col in df_copy.columns:
            df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
            colonnes_existantes.append(col)
        else:
            logger.warning(f"[FiltrageDate] Colonne '{col}' non trouvée. Ignorée.")

    if not colonnes_existantes:
        logger.error("[FiltrageDate] Aucune des colonnes spécifiées n'existe dans le DataFrame.")
        return df_copy

    # Extraire la première date non nulle
    df_copy['Premiere_date'] = df_copy[colonnes_existantes].bfill(axis=1).iloc[:, 0]

    # Filtrer selon l'année spécifiée
    df_filtre = df_copy[df_copy['Premiere_date'].dt.year == annee]

    logger.info(
        f"[FiltrageDate] {len(df_filtre)} lignes conservées avec année = {annee} "
        f"dans les colonnes {colonnes_existantes}"
    )

    # Gestion de la colonne temporaire
    if isinstance(garder_colonne, str):
        df_filtre = df_filtre.rename(columns={"Premiere_date": garder_colonne})
    elif not garder_colonne:
        df_filtre = df_filtre.drop(columns="Premiere_date")

    return df_filtre


# Filtrer par semaine épidémiologique
def filtrer_par_semaine(
    df: pd.DataFrame,
    colonnes_semaine: Optional[str] = None,
    semaines: Optional[Union[int, list, tuple]] = None,
    condition: Optional[pd.Series] = None,
    colonnes_a_garder: Optional[list[str]] = None,
    tri_par: Optional[Union[str, list[str]]] = None,
    ordre_croissant: bool = True
) -> pd.DataFrame:
    """
    Filtre un DataFrame de façon flexible :
    - par numéro de semaine (avec interprétation intelligente des tuples)
    - par condition booléenne personnalisée
    - avec sélection de colonnes et tri optionnel

    Paramètres
    ----------
    df : pd.DataFrame
        Le DataFrame à filtrer.
    colonnes_semaine : str ou None
        Nom de la colonne contenant le numéro de la semaine (ex: 'Num_semaine_epi').
        Obligatoire si `semaines` est spécifié.
    semaines : int, list, tuple ou None
        - int         : une seule semaine
        - tuple       : (début, fin), (début,), (,fin)
        - list        : liste explicite de semaines
    condition : pd.Series ou None
        Une condition booléenne personnalisée pour filtrer les lignes (ex: df['Province'] == 'Equateur').
    colonnes_a_garder : list[str] ou None
        Colonnes à retourner. Si None, toutes les colonnes sont conservées.
    tri_par : str ou list[str] ou None
        Nom(s) de colonnes pour trier le résultat.
    ordre_croissant : bool
        Tri croissant si True, décroissant sinon.

    Retour
    ------
    pd.DataFrame
        DataFrame filtré, avec colonnes sélectionnées et triées si demandé.
    """
    df_filtre = df.copy()
    lignes_avant = len(df_filtre)

    # ✅ Filtrage par semaine
    if semaines is not None:
        if colonnes_semaine is None:
            raise ValueError("Le paramètre 'colonnes_semaine' est requis si 'semaines' est spécifié.")
        if colonnes_semaine not in df.columns:
            raise KeyError(f"La colonne '{colonnes_semaine}' est absente du DataFrame.")

        if isinstance(semaines, int):
            condition_semaine = df_filtre[colonnes_semaine] == semaines
            logging.info(f"✅ Filtrage : semaine == {semaines}")

        elif isinstance(semaines, tuple):
            if len(semaines) == 1:
                condition_semaine = df_filtre[colonnes_semaine] >= semaines[0]
                logging.info(f"✅ Filtrage : semaine >= {semaines[0]}")
            elif len(semaines) == 2:
                min_sem, max_sem = semaines
                if min_sem is not None and max_sem is not None:
                    condition_semaine = df_filtre[colonnes_semaine].between(min_sem, max_sem)
                    logging.info(f"✅ Filtrage : {min_sem} <= semaine <= {max_sem}")
                elif min_sem is not None:
                    condition_semaine = df_filtre[colonnes_semaine] >= min_sem
                    logging.info(f"✅ Filtrage : semaine >= {min_sem}")
                elif max_sem is not None:
                    condition_semaine = df_filtre[colonnes_semaine] <= max_sem
                    logging.info(f"✅ Filtrage : semaine <= {max_sem}")
                else:
                    condition_semaine = pd.Series([True] * len(df_filtre), index=df_filtre.index)
                    logging.info(f"⚠️ Tuple semaines vide ou inutile, pas de filtrage appliqué.")
            else:
                raise ValueError("Tuple 'semaines' invalide : il doit contenir au plus 2 éléments.")

        elif isinstance(semaines, list):
            condition_semaine = df_filtre[colonnes_semaine].isin(semaines)
            logging.info(f"✅ Filtrage : semaines dans {semaines}")

        else:
            raise TypeError("Le paramètre 'semaines' doit être un int, list ou tuple.")

        df_filtre = df_filtre[condition_semaine]

    # ✅ Filtrage par condition personnalisée
    if condition is not None:
        df_filtre = df_filtre.loc[condition]
        logging.info("✅ Filtrage par condition personnalisée appliqué.")

    # ✅ Colonnes à garder
    if colonnes_a_garder:
        colonnes_existantes = [col for col in colonnes_a_garder if col in df_filtre.columns]
        colonnes_manquantes = set(colonnes_a_garder) - set(colonnes_existantes)

        df_filtre = df_filtre[colonnes_existantes]
        logging.info(f"✅ Colonnes conservées : {colonnes_existantes}")
        if colonnes_manquantes:
            logging.warning(f"⚠️ Colonnes absentes ignorées : {list(colonnes_manquantes)}")
    else:
        logging.info("ℹ️ Aucune colonne spécifiée : toutes les colonnes sont conservées.")

    # ✅ Tri
    if tri_par:
        colonnes_tri = [tri_par] if isinstance(tri_par, str) else tri_par
        colonnes_tri_valides = [col for col in colonnes_tri if col in df_filtre.columns]

        if colonnes_tri_valides:
            df_filtre = df_filtre.sort_values(by=colonnes_tri_valides, ascending=ordre_croissant)
            logging.info(f"✅ Tri appliqué sur {colonnes_tri_valides} (ordre croissant : {ordre_croissant})")
        else:
            logging.warning(f"⚠️ Aucune des colonnes de tri '{tri_par}' n'existe dans le DataFrame.")

    lignes_apres = len(df_filtre)
    logging.info(f"📊 Lignes avant filtrage : {lignes_avant}")
    logging.info(f"📉 Lignes après filtrage : {lignes_apres}")

    return df_filtre

# Filtrage
def filtrer_par_nullite(df: pd.DataFrame, colonnes: Union[str, List[str], pd.Series], mode: str = "notnull") -> pd.DataFrame:
    """
    Retourne les lignes d'un DataFrame selon que les colonnes soient nulles ou non.
    Utilise get_target_columns pour gérer les colonnes (y compris 'Unnamed').
    """
    # Si on reçoit une Series → on prend son nom
    if isinstance(colonnes, pd.Series):
        colonnes = colonnes.name

    # Résolution via get_target_columns
    colonnes_valides = get_target_columns(df, colonnes, allow_all_if_none=False)

    if not colonnes_valides:
        logger.warning("⚠️ Aucune colonne valide trouvée pour appliquer le filtre.")
        return df.iloc[0:0].copy()  # DataFrame vide

    # Application du masque
    if mode == "notnull":
        masque = df[colonnes_valides].notnull().all(axis=1)
    elif mode == "isnull":
        masque = df[colonnes_valides].isnull().any(axis=1)
    else:
        raise ValueError("Le paramètre 'mode' doit être 'notnull' ou 'isnull'.")

    result = df.loc[masque].reset_index(drop=True)

    logger.warning(f"Affichage des lignes (mode={mode}) pour colonnes {colonnes_valides} : {len(result)} lignes trouvées")

    return result
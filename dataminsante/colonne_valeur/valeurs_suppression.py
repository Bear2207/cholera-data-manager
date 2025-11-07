# -*- coding: utf-8 -*-
# dataminsante/colonne_valeur/valeurs_suppression.py

# Notice : Pour le module de suppression des valeurs

import pandas as pd
import os
import logging
from typing import Optional, Union, List, Literal
from dataminsante.colonne_valeur.valeurs_nettoyage import get_target_columns


# Configuration du logger par défaut
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# gerer_doublons
def gerer_doublons_avance(
    df: pd.DataFrame,
    colonnes_inclues: Optional[List[str]] = None,
    colonnes_exclues: Optional[List[str]] = None,
    normaliser: bool = True,
    type_normalisation: Literal["lower", "capitalize", "upper", None] = "capitalize",
    keep: Union[str, bool] = "first",
    mode: Literal['afficher', 'compter_lignes', 'compter_groupes', 'detail', 'nettoyer'] = 'afficher',
    marquer: bool = False,
    supprimer: bool = False,
    export_path: Optional[str] = None,
    tri_ascendant: bool = True,
    reset_index: bool = True,
    logger: Optional[logging.Logger] = None
) -> Union[pd.DataFrame, int, dict]:
    """
    Détecte, affiche ou compte les doublons dans un DataFrame selon différents modes d'analyse.

    Paramètres
    ----------
    df : pd.DataFrame
        Le DataFrame à analyser pour les doublons.

    colonnes_inclues : list[str], optionnel
        Liste explicite des colonnes à inclure pour la détection. Prioritaire sur colonnes_exclues.

    colonnes_exclues : list[str], optionnel
        Liste des colonnes à ignorer (seulement si colonnes_inclues est None).

    normaliser : bool, optionnel, défaut True
        Si True, applique un nettoyage sur les colonnes ciblées (trim + minuscule) pour éviter les doublons non détectés
        à cause de différences de casse ou d'espacement.

    keep : {'first', 'last', False}, optionnel, défaut 'first'
        Stratégie de conservation des doublons :
        - 'first' : garde la première occurrence,
        - 'last' : garde la dernière occurrence,
        - False : considère toutes les occurrences comme doublons.

    mode : {'afficher', 'compter_lignes', 'compter_groupes', 'detail'}, optionnel, défaut 'afficher'
        Mode de retour :
        - 'afficher' : retourne un DataFrame contenant toutes les lignes en doublon (selon les colonnes), trié.,
        - 'compter_lignes' : retourne un entier représentant le nombre total de lignes en doublon (y compris les répétitions),
        - 'compter_groupes' : retourne un entier indiquant le nombre de groupes distincts de doublons (valeurs identiques),
        - 'detail' : retourne un dictionnaire de synthèse :
            * 'groupes' : nombre de groupes de doublons,
            * 'lignes_dupliquees' : nombre total de lignes doublonnées.
        - 'nettoyer' : supprime les doublons du DataFrame et retourne le DataFrame nettoyé.

    marquer : bool, optionnel, défaut False
        Si True, ajoute une colonne "est_doublon" dans le DataFrame.

    supprimer : bool, optionnel, défaut False
        Si True, supprime directement les doublons du DataFrame.

    export_path : str, optionnel
        Si défini, exporte les doublons détectés vers un fichier .csv ou .xlsx.

    tri_ascendant : bool, optionnel, défaut True
        Trie les doublons dans le mode 'afficher'.

    reset_index : bool, optionnel, défaut True
        Réinitialise l'index dans le mode 'afficher' pour un rendu lisible.

    logger : logging.Logger, optionnel
        Logger pour le suivi. Si None, aucun log.

    Retours
    -------
    Union[pd.DataFrame, int, dict]
        Résultat selon le mode sélectionné.

    Exceptions
    ----------
    ValueError : si le mode ou le paramètre `keep` est invalide.
    """
    if df.empty:
        if logger:
            logger.warning("Le DataFrame fourni est vide.")
        return pd.DataFrame()

    df = df.copy()
    # Fonction utilitaire pour gérer les colonnes cibles
    colonnes_inclues = get_target_columns(df, colonnes_inclues)

    if colonnes_inclues:
        colonnes = colonnes_inclues
    else:
        colonnes = [col for col in df.columns if not (colonnes_exclues and col in colonnes_exclues)]

    colonnes_invalides = [col for col in colonnes if col not in df.columns]
    if colonnes_invalides:
        raise ValueError(f"Colonnes invalides : {colonnes_invalides}")

    if normaliser:
        for col in colonnes:
            if df[col].dtype == object:
                if type_normalisation == "lower":
                    df[col] = df[col].astype(str).str.strip().str.lower()
                elif type_normalisation == "capitalize":
                    df[col] = df[col].astype(str).str.strip().str.capitalize()
                elif type_normalisation == "upper":
                    df[col] = df[col].astype(str).str.strip().str.upper()

    masque_doublons = df.duplicated(subset=colonnes, keep=keep)

    if marquer:
        df['est_doublon'] = masque_doublons

    if supprimer:
        nb = masque_doublons.sum()
        if nb == 0:
            if logger:
                logger.warning("Aucun doublon détecté à supprimer.")
        else:
            df = df[~masque_doublons]
            if logger:
                logger.info(f"{nb} doublons supprimés.")

    doublons = df[masque_doublons]

    if export_path and not doublons.empty:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        if export_path.endswith('.xlsx'):
            doublons.to_excel(export_path, index=False)
        else:
            doublons.to_csv(export_path, index=False)
        if logger:
            logger.info(f"Doublons exportés vers : {export_path}")

    if mode == 'afficher':
        resultat = doublons.sort_values(by=colonnes, ascending=tri_ascendant)
        return resultat.reset_index(drop=True) if reset_index else resultat

    elif mode == 'compter_lignes':
        return masque_doublons.sum()

    elif mode == 'compter_groupes':
         return df[masque_doublons][colonnes].drop_duplicates().shape[0]

    elif mode == 'detail':
        total = masque_doublons.sum()
        groupes = df[masque_doublons][colonnes].drop_duplicates().shape[0]
        return {
            'groupes': groupes,
            'lignes_dupliquees': total
        }
    elif mode == 'nettoyer':
        # supprime les doublons du df (selon keep) et renvoie la df nettoyée
        df_nettoye = df.drop_duplicates(subset=colonnes, keep=keep).reset_index(drop=True) if reset_index else df.drop_duplicates(subset=colonnes, keep=keep)
        return df_nettoye
    
    else:
        raise ValueError(f"Mode non reconnu : {mode}")


# -*- coding: utf-8 -*-

# dataminsante/analyse/statistiques_descriptives.py

import pandas as pd
from typing import List, Optional, Union, Dict, Callable, Any
import logging

# Setup logger pour ce module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Vérifie l'existence des colonnes dans le df
# et gère les colonnes supplémentaires si nécessaire
def _verifier_colonnes(
    df: pd.DataFrame,
    colonnes: Union[str, List[str], None],
    colonnes_supplementaires: Union[str, List[str], None] = None,
    allow_all_if_none: bool = False
) -> List[str]:
    """
    Vérifie et résout les colonnes demandées dans un DataFrame.
    - None : retourne toutes les colonnes si allow_all_if_none=True, sinon []
    - str  : retourne une liste avec la colonne si elle existe
    - list : retourne seulement celles présentes
    Les colonnes absentes sont loggées en warning.
    """

    # Normalisation des entrées
    if colonnes is None:
        colonnes = []
    elif isinstance(colonnes, str):
        colonnes = [colonnes]

    if colonnes_supplementaires is None:
        colonnes_supplementaires = []
    elif isinstance(colonnes_supplementaires, str):
        colonnes_supplementaires = [colonnes_supplementaires]

    colonnes_totales = colonnes + colonnes_supplementaires

    if not colonnes_totales:  # cas None ou []
        return df.columns.tolist() if allow_all_if_none else []

    # Filtrage des colonnes existantes
    result = [col for col in colonnes_totales if col in df.columns]
    missing = set(colonnes_totales) - set(result)

    if missing:
        logger.warning(f"❗ Colonnes non trouvées dans le DataFrame : {list(missing)}")

    return result

# Compte les occurrences par combinaison de catégories avec filtre sur un seuil minimal
def compter_par_plusieurs_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Compte les occurrences groupées par plusieurs colonnes catégorielles et applique un filtre sur le nombre minimal.
    """
    colonnes = _verifier_colonnes(df, colonnes)
    counts = df.groupby(colonnes, dropna=False).size().reset_index(name='Nombre de cas')
    filtered = counts[counts['Nombre de cas'] >= seuil_min].reset_index(drop=True)
    return filtered

# Compte le nombre de valeurs uniques dans une colonne pour chaque modalité ou combinaison de catégories
def compter_valeurs_uniques_par_categorie(
    df: pd.DataFrame,
    colonnes_categories: Union[str, List[str]],
    colonne_valeur: str,
    dropna: bool = False
) -> pd.DataFrame:
    """
    Compte le nombre de valeurs uniques dans 'colonne_valeur' pour chaque modalité ou combinaison de 'colonnes_categories'.

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame d'entrée.
    colonnes_categories : str ou List[str]
        Une ou plusieurs colonnes pour le groupement.
    colonne_valeur : str
        La colonne dont on compte les valeurs uniques.
    dropna : bool, default=False
        Contrôle la gestion des NaN dans le groupby (comme dropna de pandas).

    Returns
    -------
    pd.DataFrame
        Un DataFrame avec les colonnes de catégories + 'Nombre_valeurs_uniques'.
    """
    # Vérification des colonnes
    colonnes = _verifier_colonnes(df, colonnes_categories, colonne_valeur)
    
    # GroupBy + nunique
    resultat = (
        df.groupby(colonnes, dropna=dropna)[colonne_valeur]
          .nunique(dropna=dropna)
          .reset_index(name='Nombre_valeurs_uniques')
    )
    
    logger.info(
        f"[INFO] Comptage des valeurs uniques de '{colonne_valeur}' par {colonnes}. "
        f"Nombre de groupes trouvés : {len(resultat)}"
    )
    
    return resultat
# Affiche les valeurs uniques pour une ou plusieurs colonnes d’un DataFrame
def afficher_valeurs_uniques(df: pd.DataFrame, colonnes: Union[str, List[str]]) -> Dict[str, List[str]]:
    """
    Affiche les valeurs uniques pour une ou plusieurs colonnes d’un DataFrame.

    Args:
        df (pd.DataFrame) : DataFrame à analyser.
        colonnes (str ou list[str]) : Nom de la colonne ou liste de colonnes.

    Returns:
        dict : Dictionnaire {colonne: liste des valeurs uniques triées (en str)}
    """
    if isinstance(colonnes, str):
        colonnes = [colonnes]

    resultats = {}

    for col in colonnes:
        if col in df.columns:
            uniques = df[col].dropna().unique()

            # Conversion sécurisée en str pour éviter les erreurs de tri
            uniques_str = sorted([str(val) for val in uniques])

            logging.info(f"🟦 {col} ({len(uniques_str)} valeurs uniques) :")
            for val in uniques_str:
                logging.info(f"   * {val}")

            resultats[col] = uniques_str
        else:
            logging.warning(f"⚠️ Colonne '{col}' non trouvée dans le DataFrame.")

    # return resultats

# Compte le nombre de combinaisons uniques simultanées des colonnes_valeurs
def compter_combinaisons_uniques_par_categories(
    df: pd.DataFrame,
    colonnes_categories: Union[str, List[str]],
    colonnes_valeurs: Union[str, List[str]],
    dropna: bool = False
) -> pd.DataFrame:
    """
    Compte le nombre de combinaisons uniques simultanées des colonnes_valeurs
    pour chaque modalité ou combinaison dans colonnes_categories.

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame source.
    colonnes_categories : str ou List[str]
        Colonnes sur lesquelles grouper.
    colonnes_valeurs : str ou List[str]
        Colonnes dont on compte les combinaisons uniques.
    dropna : bool
        Supprime ou pas les NaN dans groupby.

    Returns
    -------
    pd.DataFrame
        DataFrame avec colonnes_categories + colonne 'Nombre_combinaisons_uniques'.
    """
    if isinstance(colonnes_categories, str):
        colonnes_categories = [colonnes_categories]
    if isinstance(colonnes_valeurs, str):
        colonnes_valeurs = [colonnes_valeurs]

    # Vérification colonnes
    colonnes_a_verifier = colonnes_categories + colonnes_valeurs
    colonnes_manquantes = [c for c in colonnes_a_verifier if c not in df.columns]
    if colonnes_manquantes:
        raise ValueError(f"Colonnes manquantes dans df : {colonnes_manquantes}")

    # Fonction interne pour compter les tuples uniques dans groupe
    def nb_combinaisons_uniques(group):
        # dropna optionnel sur le sous-DataFrame
        sous_df = group[colonnes_valeurs]
        if dropna:
            sous_df = sous_df.dropna()
        return len(sous_df.drop_duplicates())

    # Groupby avec agg custom
    resultat = (
        df.groupby(colonnes_categories, dropna=dropna)
          .apply(nb_combinaisons_uniques)
          .reset_index(name='Nombre_combinaisons_uniques')
    )
    return resultat

# Calcule la moyenne des valeurs numériques groupées par catégories, avec seuil minimal
def moyenne_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    colonne_valeur: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Calcule la moyenne des valeurs numériques groupées par plusieurs colonnes catégorielles, avec un seuil minimal.
    """
    colonnes = _verifier_colonnes(df, colonnes, colonne_valeur)
    moyennes = df.groupby(colonnes, dropna=False)[colonne_valeur].agg(['mean', 'count']).reset_index()
    moyennes = moyennes.rename(columns={'mean': 'Moyenne', 'count': 'Nombre'})
    if seuil_min > 0:
        moyennes = moyennes[moyennes['Nombre'] >= seuil_min]
    return moyennes.reset_index(drop=True)

# Calcule le mode des valeurs groupées par catégories, avec seuil minimal
def mode_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    colonne_valeur: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Calcule le mode des valeurs groupées par colonnes catégorielles, avec un seuil minimal.
    """
    # Vérification des colonnes (je suppose que _verifier_colonnes lève une exception si pas trouvé)
    colonnes = _verifier_colonnes(df, colonnes, colonne_valeur)

    def mode_unique(series: pd.Series) -> Union[str, float, int, None]:
        m = series.mode()
        return m.iloc[0] if not m.empty else None

    group = df.groupby(colonnes, dropna=False)[colonne_valeur]
    result = group.agg(Mode=mode_unique, Nombre='count').reset_index()
    if seuil_min > 0:
        result = result[result['Nombre'] >= seuil_min]
    return result.reset_index(drop=True)


# Calcule la médiane des valeurs numériques par catégories, avec seuil minimal
def mediane_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    colonne_valeur: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Calcule la médiane des valeurs numériques groupées par plusieurs colonnes catégorielles, avec un seuil minimal.
    """
    colonnes = _verifier_colonnes(df, colonnes, colonne_valeur)
    result = df.groupby(colonnes, dropna=False)[colonne_valeur].agg(['median', 'count']).reset_index()
    result = result.rename(columns={'median': 'Mediane', 'count': 'Nombre'})
    if seuil_min > 0:
        result = result[result['Nombre'] >= seuil_min]
    return result.reset_index(drop=True)

# Calcule l'écart-type, min, max, moyenne par catégories, avec seuil minimal
def ecart_type_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    colonne_valeur: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Calcule l'écart-type, min, max et moyenne des valeurs groupées par catégories, avec un seuil minimal.
    """
    colonnes = _verifier_colonnes(df, colonnes, colonne_valeur)
    stats = df.groupby(colonnes, dropna=False)[colonne_valeur].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
    stats = stats.rename(columns={
        'mean': 'Moyenne', 'std': 'Ecart_type', 'min': 'Minimum', 'max': 'Maximum', 'count': 'Nombre'
    })
    if seuil_min > 0:
        stats = stats[stats['Nombre'] >= seuil_min]
    return stats.reset_index(drop=True)

# Regroupe les individus en classes d'âge prédéfinies
def repartition_par_classes(
    df: pd.DataFrame,
    colonne_age: str,
    classes: Union[List[int], pd.Series],
    label_colonne: str = 'Classe_age'
) -> pd.DataFrame:
    """
    Regroupe les valeurs d'âge selon des classes définies, avec des labels au format 'min-max'.
    """
    if colonne_age not in df.columns:
        raise ValueError(f"[ERREUR] La colonne '{colonne_age}' n'existe pas dans le DataFrame.")
    if not pd.api.types.is_numeric_dtype(df[colonne_age]):
        raise TypeError(f"[ERREUR] La colonne '{colonne_age}' doit être numérique.")

    if not isinstance(classes, (list, tuple, pd.Series)):
        raise TypeError("[ERREUR] 'classes' doit être une liste, un tuple ou une série pandas.")
    if len(classes) < 2:
        raise ValueError("[ERREUR] 'classes' doit contenir au moins deux bornes.")
    if any(classes[i] >= classes[i+1] for i in range(len(classes)-1)):
        raise ValueError("[ERREUR] Les bornes de 'classes' doivent être strictement croissantes.")

    df = df.copy()
    labels = [f"{classes[i]}-{classes[i+1]}" for i in range(len(classes)-1)]
    df[label_colonne] = pd.cut(df[colonne_age], bins=classes, labels=labels, right=True, include_lowest=True)
    return df

# Résume les indicateurs statistiques principaux par catégories
def resume_statistique_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]],
    colonne_valeur: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Résume moyenne, médiane, écart-type, min et max par catégories avec un seuil minimal.
    """
    colonnes = _verifier_colonnes(df, colonnes, colonne_valeur)
    result = df.groupby(colonnes, dropna=False)[colonne_valeur].agg(['mean', 'median', 'std', 'min', 'max', 'count']).reset_index()
    result = result.rename(columns={
        'mean': 'Moyenne', 'median': 'Mediane', 'std': 'Ecart_type',
        'min': 'Minimum', 'max': 'Maximum', 'count': 'Nombre'
    })
    if seuil_min > 0:
        result = result[result['Nombre'] >= seuil_min]
    return result.reset_index(drop=True)

# Calcule la proportion de chaque catégorie ou combinaison de catégories
def proportion_par_categories(
    df: pd.DataFrame,
    colonnes: Union[str, List[str]]
) -> pd.DataFrame:
    """
    Calcule la proportion (en %) de chaque catégorie ou combinaison de catégories.
    """
    colonnes = _verifier_colonnes(df, colonnes)
    counts = df.groupby(colonnes, dropna=False).size().reset_index(name='Nombre')
    total = counts['Nombre'].sum()
    counts['Proportion (%)'] = counts['Nombre'] / total * 100
    return counts.sort_values('Proportion (%)', ascending=False).reset_index(drop=True)

def tableau_croise_dynamique(
    df: pd.DataFrame,
    lignes: Union[str, List[str]],
    colonnes: Union[str, List[str]],
    valeurs: Optional[Union[str, List[str]]] = None,
    aggfunc: Union[str, Dict[str, Union[str, List[str]]], Callable] = "count",
    fill_value: Any = 0,
    margins: bool = False,
    margins_name: str = "Total",
    dropna: bool = False
) -> pd.DataFrame:
    """
    Crée un tableau croisé dynamique (TCD) similaire à Excel avec contrôle des colonnes.

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame source.
    lignes : str ou List[str]
        Une ou plusieurs colonnes à utiliser comme index (lignes).
    colonnes : str ou List[str]
        Une ou plusieurs colonnes à utiliser comme en-têtes de colonnes.
    valeurs : str ou List[str], optional
        Colonne(s) contenant les valeurs à agréger.
        Si None, effectue un comptage.
    aggfunc : str, dict ou Callable, default="count"
        Fonction(s) d’agrégation : "sum", "count", "mean", etc., ou dictionnaire de mapping.
    fill_value : Any, default=0
        Valeur de remplacement des cellules vides (NaN).
    margins : bool, default=False
        Ajoute les totaux par ligne et colonne.
    margins_name : str, default="Total"
        Nom de la ligne et colonne de total.
    dropna : bool, default=False
        Inclut ou exclut les combinaisons de valeurs manquantes.

    Returns
    -------
    pd.DataFrame
        Un tableau croisé dynamique prêt à être affiché ou exporté.
    """
    # Vérification des colonnes
    colonnes_a_verifier = []
    for item in [lignes, colonnes, valeurs]:
        if item:
            if isinstance(item, str):
                colonnes_a_verifier.append(item)
            elif isinstance(item, list):
                colonnes_a_verifier.extend(item)

    _verifier_colonnes(df, colonnes_a_verifier)

    # Création du pivot table
    table = pd.pivot_table(
        data=df,
        index=lignes,
        columns=colonnes,
        values=valeurs,
        aggfunc=aggfunc,
        fill_value=fill_value,
        margins=margins,
        margins_name=margins_name,
        dropna=dropna
    )

    # Réinitialisation de l’index pour un DataFrame plat
    table_reset = table.reset_index()

    logger.info(
        f"[TCD] Tableau croisé dynamique créé avec index={lignes}, colonnes={colonnes}, "
        f"valeurs={valeurs}, aggfunc={aggfunc}, margins={margins}"
    )

    return table_reset


# Agrège les valeurs numériques par période (hebdo, mois, etc.)
def evolution_temporelle(
    df: pd.DataFrame,
    colonne_temps: str,
    colonne_valeur: str,
    freq: str = 'W'
) -> pd.DataFrame:
    """
    Agrège les valeurs numériques par période (jour, semaine, mois, etc.).
    """
    df = df.copy()
    df[colonne_temps] = pd.to_datetime(df[colonne_temps], errors='coerce')
    n_nuls = df[colonne_temps].isna().sum()
    if n_nuls > 0:
        logger.warning(f"[WARN] {n_nuls} valeurs invalides converties en NaT dans la colonne '{colonne_temps}'.")
    df = df.dropna(subset=[colonne_temps])

    if df.empty:
        logger.warning("[WARN] Le DataFrame est vide après suppression des dates invalides.")

    resultat = df.resample(freq, on=colonne_temps)[colonne_valeur].sum().reset_index()
    return resultat.rename(columns={colonne_valeur: 'Total'})

# Détecte les valeurs aberrantes dans une colonne numérique avec la méthode IQR
def detecter_outliers(
    df: pd.DataFrame,
    colonne_valeur: str
) -> pd.DataFrame:
    """
    Détecte les outliers dans une colonne numérique en utilisant la méthode de l'IQR.
    Retourne les lignes du DataFrame avec des outliers.
    """
    if colonne_valeur not in df.columns:
        raise ValueError(f"Colonne '{colonne_valeur}' introuvable dans le DataFrame.")

    if not pd.api.types.is_numeric_dtype(df[colonne_valeur]):
        raise TypeError(f"La colonne '{colonne_valeur}' doit être numérique.")

    Q1 = df[colonne_valeur].quantile(0.25)
    Q3 = df[colonne_valeur].quantile(0.75)
    IQR = Q3 - Q1
    borne_basse = Q1 - 1.5 * IQR
    borne_haute = Q3 + 1.5 * IQR
    outliers = df[(df[colonne_valeur] < borne_basse) | (df[colonne_valeur] > borne_haute)]

    logger.info(f"Q1={Q1:.3f}, Q3={Q3:.3f}, IQR={IQR:.3f}")
    logger.info(f"Bornes outliers: [{borne_basse:.3f}, {borne_haute:.3f}]")
    logger.info(f"Nombre d’outliers détectés : {len(outliers)}")

    return outliers

# Calcule la matrice de corrélation entre colonnes numériques sélectionnées
def correlation_variables(
    df: pd.DataFrame,
    colonnes_numeriques: Union[str, List[str]]
) -> pd.DataFrame:
    """
    Calcule la matrice de corrélation entre les colonnes numériques.
    """
    colonnes = _verifier_colonnes(df, colonnes_numeriques)
    return df[colonnes].corr()


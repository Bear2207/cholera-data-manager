# -*- coding: utf-8 -*-
# dataminsante/analyse/classification_maladie.py

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Union
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Détection du chemin en fonction de l'environnement (script ou notebook)
try:
    base_dir = Path(__file__).resolve().parents[2] / "data"
except NameError:
    base_dir = Path().resolve() / "data"

mapping_file_path = base_dir / "Replace_values.xlsx"

# Fonction pour construire les critères de classification depuis un fichier de mapping
def critere_classification_mapping(
    fichier_mapping: Union[str, Path] = mapping_file_path,
    variable_cible: Union[str, List[str]] = ""
) -> Tuple[Dict[str, List[str]], Dict[str, bool]]:
    """
    Construit un dictionnaire de critères depuis un fichier de mapping Excel.

    Args:
        fichier_mapping (str | Path): Chemin vers le fichier Excel de mapping.
        variable_cible (str | list[str]): Nom ou liste de noms de variables (colonnes cibles du DataFrame).

    Returns:
        Tuple[
            critere: Dict[str, List[str]],        # { "issue": [...], "serotype": [...] }
            regex_mode: Dict[str, bool]           # { "issue": True, "serotype": False }
        ]
    """
    fichier_mapping = Path(fichier_mapping)

    if not fichier_mapping.exists():
        raise FileNotFoundError(f"Fichier de mapping introuvable : {fichier_mapping}")

    try:
        mapping = pd.read_excel(fichier_mapping, dtype=str)
        # Nettoyer les lignes incomplètes sur colonnes essentielles
        mapping = mapping.dropna(subset=["Original", "Variable", "Regex_valide"])
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier mapping : {e}")
        raise

    # Normalisation des noms de colonnes
    mapping.columns = [col.strip().lower() for col in mapping.columns]

    # Vérifie la présence des colonnes essentielles
    colonnes_attendues = {"original", "variable", "regex_valide"}
    if not colonnes_attendues.issubset(set(mapping.columns)):
        raise ValueError(f"Colonne(s) manquante(s) dans le mapping : {colonnes_attendues}")

    # Assurer que variable_cible est une liste
    if isinstance(variable_cible, str):
        variable_cible = [variable_cible]

    critere: Dict[str, List[str]] = {}
    regex_mode: Dict[str, bool] = {}

    for var in variable_cible:
        nom_var = var.strip().lower()
        filtre = mapping[mapping["variable"].str.strip().str.lower() == nom_var]

        if filtre.empty:
            logger.warning(f"[Mapping] Aucun critère trouvé pour la variable '{var}'")
            continue

        motifs = filtre["original"].dropna().str.strip().tolist()
        regex = filtre["regex_valide"].str.strip().str.upper().eq("VRAI").any()

        critere[nom_var] = motifs
        regex_mode[nom_var] = regex

    if not critere:
        raise ValueError("Aucun critère valide trouvé pour les variables fournies.")

    logger.info(f"[Mapping] Critères chargés pour les variables : {list(critere.keys())}")
    return critere, regex_mode

def charger_mapping(
    fichier_mapping: Union[str, Path] = mapping_file_path
) -> Dict[str, Dict[str, str]]:
    """
    Charge le fichier Excel de mapping et retourne un dictionnaire de la forme :
    variable -> {original: renamed}

    - Vérifie la présence des colonnes attendues.
    - Supprime les doublons sur les colonnes "original".
    - Journalise les variables mappées.
    """
    # Lecture du fichier
    df_map = pd.read_excel(fichier_mapping, dtype=str)
    df_map.columns = [c.strip().lower() for c in df_map.columns]

    # Vérification des colonnes attendues
    colonnes_attendues = {"original", "renamed", "variable", "regex_valide"}
    if not colonnes_attendues.issubset(set(df_map.columns)):
        raise ValueError(f"Le fichier mapping doit contenir les colonnes : {colonnes_attendues}")

    # Nettoyage des lignes incomplètes
    df_map = df_map.dropna(subset=["original", "renamed", "variable", "regex_valide"])

    mapping_var = {}
    for var, group in df_map.groupby("variable"):
        group = group.drop_duplicates(subset="original")  # Suppression des doublons
        mapping_var[var] = dict(zip(group["original"].str.lower(), group["renamed"]))

    logger.info(f"🔁 Mapping chargé pour {len(mapping_var)} variables : {list(mapping_var.keys())}")
    return mapping_var

def est_cas_suspect(
    df: pd.DataFrame,
    critere: dict,
    regex_mode: bool = False,
    fichier_mapping: Union[str, Path] = mapping_file_path,
    nom_colonne: str = "est_cas_suspect",
) -> pd.DataFrame:
    """
    Identifie les cas suspects dans un DataFrame selon des critères définis colonne par colonne.

    La logique utilisée est un ET logique (AND) sur l'ensemble des conditions spécifiées dans `critere`.

    En mode `regex_mode=True`, les valeurs du dictionnaire `critere` sont interprétées comme des motifs à
    comparer via un fichier de mapping (`fichier_mapping`) contenant des expressions régulières
    permettant de normaliser les valeurs (colonnes : 'original', 'renamed', 'variable').

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame à analyser.
    critere : dict
        Un dictionnaire où chaque clé est une colonne du DataFrame, et chaque valeur est :
        - une chaîne (str), ou
        - une liste de chaînes, représentant les valeurs à tester dans la colonne concernée.
    regex_mode : bool, optional
        Si True, les valeurs du critère sont traitées avec des expressions régulières
        via le fichier `fichier_mapping`. Par défaut False.
    fichier_mapping : str or Path, optional
        Chemin vers le fichier Excel de mapping contenant les colonnes 'original', 'renamed', et 'variable'.
        Utilisé uniquement si `regex_mode=True`.
    nom_colonne : str, optional
        Nom de la colonne ajoutée au DataFrame pour indiquer si la ligne correspond à un cas suspect.

    Returns
    -------
    pd.DataFrame
        Une copie du DataFrame d'origine avec une nouvelle colonne booléenne `nom_colonne`
        indiquant True pour les lignes correspondant aux critères (cas suspects), False sinon.

    Exemple
    -------
    >>> critere = {
    ...     "Resultat_labo_pcr": ["positif", "poitif", "posi"],
    ...     "Prelevement": "Oui"
    ... }
    >>> df_resultat = est_cas_suspect(df, critere, regex_mode=True, fichier_mapping="Replace_values.xlsx")
    """

    df = df.copy()
    
    logger.info(f"[Suspicion] Évaluation des cas suspects (regex_mode={regex_mode}) → '{nom_colonne}'")
    mask_total = pd.Series(True, index=df.index)

    if regex_mode:
        # Charger le mapping Excel
        df_map = pd.read_excel(fichier_mapping, dtype=str)
        df_map.columns = [c.strip().lower() for c in df_map.columns]
        df_map = df_map.dropna(subset=["original", "renamed", "variable"])

    for colonne, condition in critere.items():
        if colonne not in df.columns:
            logger.warning(f"⚠️ Colonne '{colonne}' absente — critère ignoré.")
            continue

        logger.info(f"🟦 Application du critère sur '{colonne}'")

        valeurs = [condition] if isinstance(condition, str) else condition
        valeurs_renommees = []

        if regex_mode:
            for val in valeurs:
                trouve = False
                val_low = val.lower()
                # Mapping uniquement pour la variable concernée
                sous_map = df_map[df_map["variable"].str.lower() == colonne.lower()]
                for _, row in sous_map.iterrows():
                    pattern = row["original"]
                    try:
                        if re.fullmatch(pattern, val_low, flags=re.IGNORECASE):
                            valeurs_renommees.append(row["renamed"])
                            logger.info(f"🔁 '{val}' matche '{pattern}' → '{row['renamed']}'")
                            trouve = True
                            break  # Une correspondance suffit
                    except re.error as e:
                        logger.warning(f"⚠️ Regex invalide '{pattern}' ignorée : {e}")
                if not trouve:
                    logger.warning(f"❗Valeur '{val}' non couverte par le mapping pour '{colonne}', conservée telle quelle.")
                    valeurs_renommees.append(val)
        else:
            valeurs_renommees = valeurs

        # Appliquer le filtre sur le DataFrame
        mask = df[colonne].astype(str).str.lower().isin([v.lower() for v in valeurs_renommees])
        mask_total &= mask

    df[nom_colonne] = mask_total
    logger.info(f"✅ {mask_total.sum()} cas suspects détectés")
    return df

def est_cas_confirme(
    df: pd.DataFrame,
    critere: dict,
    regex_mode: bool = False,
    fichier_mapping: Union[str, Path] = mapping_file_path,
    nom_colonne: str = "est_cas_confirme"
) -> pd.DataFrame:
    """
    Identifie les cas confirmés dans un DataFrame selon des critères définis colonne par colonne.

    La logique utilisée est un OU logique (OR) sur l'ensemble des conditions spécifiées dans `critere`.

    En mode `regex_mode=True`, les valeurs du dictionnaire `critere` sont interprétées comme des motifs à
    comparer via un fichier de mapping (`fichier_mapping`) contenant des expressions régulières
    permettant de normaliser les valeurs (colonnes : 'original', 'renamed', 'variable').

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame à analyser.
    critere : dict
        Un dictionnaire où chaque clé est une colonne du DataFrame, et chaque valeur est :
        - une chaîne (str),
        - une liste de chaînes, ou
        - une fonction personnalisée `callable` appliquée à chaque cellule.
    regex_mode : bool, optional
        Si True, les valeurs du critère sont traitées avec des expressions régulières
        via le fichier `fichier_mapping`. Par défaut False.
    fichier_mapping : str or Path, optional
        Chemin vers le fichier Excel de mapping contenant les colonnes 'original', 'renamed', et 'variable'.
        Utilisé uniquement si `regex_mode=True`.
    nom_colonne : str, optional
        Nom de la colonne ajoutée au DataFrame pour indiquer si la ligne correspond à un cas confirmé.

    Returns
    -------
    pd.DataFrame
        Une copie du DataFrame d'origine avec une nouvelle colonne booléenne `nom_colonne`
        indiquant True pour les lignes correspondant aux critères (cas confirmés), False sinon.

    Exemple
    -------
    >>> critere = {
    ...     "TDR_Resultat": ["positif", "poitif", "posi"],
    ...     "Resultat_labo_pcr": lambda x: x.lower() in ["positif"]
    ... }
    >>> df_resultat = est_cas_confirme(df, critere, regex_mode=True, fichier_mapping="Replace_values.xlsx")
    """
    logger.info(f"[Confirmation] Évaluation des cas confirmés (regex_mode={regex_mode}) → '{nom_colonne}'")

    df = df.copy()
    mask_total = pd.Series(False, index=df.index)

    if regex_mode:
        try:
            df_map = pd.read_excel(fichier_mapping, dtype=str)
            df_map.columns = [c.strip().lower() for c in df_map.columns]
            df_map = df_map.dropna(subset=["original", "renamed", "variable"])
        except Exception as e:
            logger.error(f"❌ Erreur de chargement du fichier de mapping : {e}")
            return df

    for colonne, condition in critere.items():
        if colonne not in df.columns:
            logger.warning(f"⚠️ [Confirmation] Colonne '{colonne}' absente — critère ignoré.")
            continue

        logger.info(f"🟦 [Confirmation] Application du critère sur '{colonne}'")
        mask = pd.Series(False, index=df.index)

        if callable(condition):
            mask = df[colonne].apply(condition)

        else:
            valeurs = [condition] if isinstance(condition, str) else condition
            valeurs_renommees = []

            if regex_mode:
                sous_map = df_map[df_map["variable"].str.lower() == colonne.lower()]
                for val in valeurs:
                    trouve = False
                    val_low = val.lower()
                    for _, row in sous_map.iterrows():
                        pattern = row["original"]
                        try:
                            if re.fullmatch(pattern, val_low, flags=re.IGNORECASE):
                                valeurs_renommees.append(row["renamed"])
                                logger.info(f"🔁 '{val}' matche '{pattern}' → '{row['renamed']}'")
                                trouve = True
                                break
                        except re.error as e:
                            logger.warning(f"⚠️ Regex invalide '{pattern}' ignorée : {e}")
                    if not trouve:
                        logger.warning(f"❗Valeur '{val}' non couverte par le mapping pour '{colonne}', conservée telle quelle.")
                        valeurs_renommees.append(val)
            else:
                valeurs_renommees = valeurs

            mask = df[colonne].astype(str).str.lower().isin([v.lower() for v in valeurs_renommees])

        mask_total |= mask

    df[nom_colonne] = mask_total
    logger.info(f"[Confirmation] ✅ {mask_total.sum()} cas confirmés détectés")
    return df

def classer_cas(
    df: pd.DataFrame,
    critere_suspect: dict,
    critere_confirme: dict,
    regex_mode: bool = False,
    nom_maladie: str = "rougeole",
    col_suspect: str = "est_cas_suspect",
    col_confirme: str = "est_cas_confirme",
    col_classification: str = "classification_auto"
) -> pd.DataFrame:
    """
    Effectue une classification automatique des cas à partir des critères suspects et confirmés.

    La classification retourne :
    - Vrai {maladie} confirmé
    - Cas suspect non confirmé
    - Cas incohérent (confirmé sans suspicion)
    - Non {maladie}

    Args:
        df (pd.DataFrame): Données d'entrée.
        critere_suspect (dict): Critères logiques AND pour suspicion.
        critere_confirme (dict): Critères logiques OR pour confirmation.
        regex_mode (bool): Active le mode regex pour les valeurs textuelles.
        nom_maladie (str): Nom de la maladie (pour les étiquettes).
        col_suspect (str): Nom de la colonne des cas suspects.
        col_confirme (str): Nom de la colonne des cas confirmés.
        col_classification (str): Colonne finale à ajouter.

    Returns:
        pd.DataFrame: DataFrame enrichi des trois colonnes de classification.
    """
    logger.info(f"[Classification] Lancement de la classification pour '{nom_maladie}'")

    df = est_cas_suspect(df, critere_suspect, regex_mode=regex_mode, nom_colonne=col_suspect)
    df = est_cas_confirme(df, critere_confirme, regex_mode=regex_mode, nom_colonne=col_confirme)

    def _classer_ligne(row):
        if row[col_suspect] and row[col_confirme]:
            return f"Vrai {nom_maladie} confirmé"
        elif row[col_suspect]:
            return "Cas suspect non confirmé"
        elif row[col_confirme]:
            return "Cas incohérent"
        else:
            return f"Non {nom_maladie}"

    df[col_classification] = df.apply(_classer_ligne, axis=1)
    logger.info(f"[Classification] Résultat dans '{col_classification}':\n{df[col_classification].value_counts()}")
    return df

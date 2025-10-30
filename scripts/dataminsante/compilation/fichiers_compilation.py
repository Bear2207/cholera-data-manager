# -*- coding: utf-8 -*-

# dataminsante/compilation/fichiers_compilation.py


import pandas as pd
import os
import logging
import re
from typing import List, Optional,Union, Dict, Tuple
from collections import defaultdict
from dataminsante.colonne_valeur.colonne_nettoyage import *
from datetime import datetime
from pathlib import Path
import fnmatch



# Configuration du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Chemins des fichiers
base_dir = Path(__file__).resolve().parents[2]
mapping_file_path = base_dir / "data" / "Rename_columns.xlsx"

"""
Fonctions utilitaires simples / basiques
- lister_fichiers_excel
- lire_fichiers_excel
- detecter_doublons_standardises
- rendre_colonnes_uniques

"""
# Lister les fichiers Excel valides dans un dossier donné
def lister_fichiers_excel(dossier_racine, motif_fichier="*LL_Rougeole.xlsx", sensible_a_la_casse=False):
    dossier = Path(dossier_racine)
    if not dossier.exists():
        raise ValueError(f"Dossier inexistant : {dossier_racine}")

    fichiers_trouves = []
    for fichier in dossier.rglob("*.xlsx"):  # récursif, uniquement fichiers Excel
        if fichier.name.startswith("~$"):  # exclusion fichiers temporaires Excel
            continue

        nom_fichier = fichier.name
        if not sensible_a_la_casse:
            if fnmatch.fnmatch(nom_fichier.lower(), motif_fichier.lower()):
                fichiers_trouves.append(fichier)
        else:
            if fnmatch.fnmatch(nom_fichier, motif_fichier):
                fichiers_trouves.append(fichier)

    logger.info(
        f"{len(fichiers_trouves)} fichiers trouvés avec motif '{motif_fichier}' "
        f"(sensible_a_la_casse={sensible_a_la_casse}) dans {dossier_racine}."
    )

    return fichiers_trouves

#  Lire les fichiers Excel 
def lire_fichiers_excel(liste_fichiers, sheet_name="Feuille1", sensible_a_la_casse=False):
    """
    Lit les fichiers Excel fournis et retourne un dictionnaire de DataFrames.
    
    :param liste_fichiers: Liste des chemins de fichiers Excel.
    :param sheet_name: Nom de la feuille à lire.
    :param sensible_a_la_casse: Booléen pour activer la sensibilité à la casse (False par défaut).
    :return: Dictionnaire {nom_fichier: DataFrame}.
    """
    donnees = {}
    for chemin in liste_fichiers:
        nom_fichier = os.path.basename(chemin)
        try:
            xl = pd.ExcelFile(chemin)
            feuilles = xl.sheet_names

            if sensible_a_la_casse:
                feuille_choisie = sheet_name if sheet_name in feuilles else None
            else:
                feuilles_lower = [f.lower() for f in feuilles]
                try:
                    idx = feuilles_lower.index(sheet_name.lower())
                    feuille_choisie = feuilles[idx]
                except ValueError:
                    feuille_choisie = None

            if feuille_choisie is None:
                raise ValueError(f"Feuille '{sheet_name}' non trouvée dans {nom_fichier}")

            df = xl.parse(sheet_name=feuille_choisie)
            donnees[nom_fichier] = df
            logger.info(f"✅ Lu : {nom_fichier} - feuille : {feuille_choisie}")
        except Exception as e:
            logger.warning(f"❌ Erreur avec {nom_fichier} : {e}")

    return donnees

# detecter_doublons_standardises
def detecter_doublons_standardises(df: pd.DataFrame, provenance: str) -> List[str]:
    """
    Détecte les noms de colonnes qui, une fois standardisés, apparaissent plusieurs fois.
    Utile pour identifier les problèmes de duplication silencieuse.

    Args:
        df: DataFrame à analyser.
        provenance: Nom du fichier ou identifiant du DataFrame.

    Returns:
        Liste des noms standardisés en doublon.
    """
    noms_standards = [standardiser_nom(c) for c in df.columns]
    compteur = defaultdict(int)
    for nom in noms_standards:
        compteur[nom] += 1
    doublons = [nom for nom, count in compteur.items() if count > 1]
    if doublons:
        logger.warning(f"[{provenance}] Colonnes standardisées en doublon détectées : {doublons}")
    return doublons

# Rendre les noms de colonnes uniques
def rendre_colonnes_uniques(cols: List[str]) -> List[str]:
    """
    Rend une liste de noms de colonnes unique en ajoutant des suffixes _01, _02...

    Args:
        cols: Liste de noms (souvent standardisés).

    Returns:
        Liste avec noms uniques.
    """
    compteur = defaultdict(int)
    noms_uniques = []
    for col in cols:
        compteur[col] += 1
        if compteur[col] == 1:
            noms_uniques.append(col)
        else:
            noms_uniques.append(f"{col}_{compteur[col]-1:02d}")
    return noms_uniques

""" 
Fonctions de traitement / transformation des données

- renommer_colonnes_avec_provenance
- afficher_colonnes_standardisees
- fusionner_colonnes_similaires
- comparer_colonnes_multiples

"""

# Renommer les colonnes avec la nouvelle colonne : provenance
def renommer_colonnes_avec_provenance(df: pd.DataFrame, provenance: str, colonnes_a_renommer: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Renomme certaines colonnes d'un DataFrame en ajoutant la provenance comme suffixe.

    Args:
        df: DataFrame original.
        provenance: Suffixe à ajouter.
        colonnes_a_renommer: Colonnes ciblées (par défaut toutes sauf "Provenance").

    Returns:
        DataFrame avec colonnes renommées.
    """
    if colonnes_a_renommer is None:
        colonnes_a_renommer = [col for col in df.columns if col != "Provenance"]

    new_cols = {}
    for col in colonnes_a_renommer:
        new_cols[col] = f"{col}_{provenance}"
    return df.rename(columns=new_cols)

# Afficher les colonnes standardisées
def afficher_colonnes_standardisees(dataframes: List[pd.DataFrame]) -> None:
    """
    Afficher dans les logs les colonnes standardisées pour chaque DataFrame.

    Args:
        dataframes (List[pd.DataFrame]): Liste de DataFrames.
    """
    logger.info("Affichage des colonnes standardisées par fichier :")
    for i, df in enumerate(dataframes):
        provenance = (
            df["Provenance"].iloc[0]
            if "Provenance" in df.columns
            else f"Fichier_{i + 1}"
        )
        cols_std = [standardiser_nom(col) for col in df.columns]
        logger.info(f"Fichier : {provenance} — Colonnes standardisées : {cols_std}")
 
# Fusionner les colonnes similaires
def fusionner_colonnes_similaires(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Fusionne les colonnes similaires des DataFrames en se basant sur un suffixe numérique.
    Gère la standardisation des noms, la vérification des doublons et l'identification de la provenance.

    Args:
        dataframes (List[pd.DataFrame]): Liste de DataFrames à fusionner.

    Returns:
        pd.DataFrame: DataFrame fusionné avec colonnes unifiées.
    """

    dataframes_renommes = []

    # --- Standardisation et vérification des doublons ---
    for df in dataframes:
        provenance = df["Provenance"].iloc[0] if "Provenance" in df.columns else "inconnu"
        noms_std = [standardiser_nom(c) for c in df.columns]
        noms_uniques = rendre_colonnes_uniques(noms_std)
        col_map = dict(zip(df.columns, noms_uniques))
        df_renamed = df.rename(columns=col_map)

        colonnes_dupliquees = df_renamed.columns[df_renamed.columns.duplicated()].tolist()
        if colonnes_dupliquees:
            raise ValueError(f"Colonnes dupliquées après renommage dans '{provenance}' : {colonnes_dupliquees}")

        dataframes_renommes.append(df_renamed)

    # --- Concaténation des DataFrames renommés ---
    df_fusionne = pd.concat(dataframes_renommes, ignore_index=True)

    # --- Regroupement et fusion des colonnes suffixées ---
    groupes = {}
    for col in df_fusionne.columns:
        if "_" in col and col.split("_")[-1].isdigit():
            base = "_".join(col.split("_")[:-1])
            groupes.setdefault(base, []).append(col)

    for base, cols in groupes.items():
        if base not in df_fusionne.columns:
            df_fusionne[base] = None
        for col in cols:
            df_fusionne[base] = df_fusionne[base].fillna(df_fusionne[col])
        df_fusionne.drop(columns=cols, inplace=True)

    # --- Suppression des colonnes vides et lignes entièrement vides ---
    colonnes_a_supprimer = [c for c in df_fusionne.columns if c.startswith("Unnamed") and df_fusionne[c].isnull().all()]
    if colonnes_a_supprimer:
        df_fusionne.drop(columns=colonnes_a_supprimer, inplace=True)

    df_fusionne.dropna(how='all', inplace=True)

    return df_fusionne

# Comparer les colonnes entre plusieurs DataFrames
def comparer_colonnes_multiples(
    dfs: Dict[str, pd.DataFrame],
    valeur_absente: Union[str, None] = "-"
) -> pd.DataFrame:
    """
    Compare les colonnes entre plusieurs DataFrames et retourne une table croisée
    indiquant la présence ou l'absence de chaque colonne.

    Args:
        dfs (Dict[str, pd.DataFrame]): 
            Dictionnaire où les clés sont les noms de jeux de données, 
            et les valeurs sont les DataFrames à comparer.
        
        valeur_absente (Union[str, None], optional): 
            Valeur à afficher si une colonne est absente dans un DataFrame. 
            Par défaut "-". Peut aussi être None ou tout autre indicateur.

    Returns:
        pd.DataFrame: 
            Tableau croisé listant toutes les colonnes uniques et indiquant 
            leur présence ou absence dans chaque DataFrame.

    Exemple :
        >>> dfs = {
        ...     "fichier_jaune": pd.DataFrame(columns=["Nom", "Age"]),
        ...     "fichier_vert": pd.DataFrame(columns=["Nom", "Sexe"]),
        ... }
        >>> resultat = comparer_colonnes_multiples(dfs)
        >>> print(resultat.to_markdown(index=False))
    """
    # Récupérer toutes les colonnes distinctes de tous les DataFrames
    toutes_colonnes = sorted(set(col for df in dfs.values() for col in df.columns))
    
    # Construire le tableau
    tableau = []
    for col in toutes_colonnes:
        ligne = {"Colonne": col}
        for nom_df, df in dfs.items():
            ligne[nom_df] = col if col in df.columns else valeur_absente
        tableau.append(ligne)

    return pd.DataFrame(tableau)

# ------------------------------------------------
# Fonction(s) principale(s) d’orchestration
# ------------------------------------------------
# Charger plusieurs fichiers Excel, nettoyer les colonnes, ajouter la provenance, et fusionner les données
def charger_fichiers_excel(
    dossier_racine: Optional[str] = None,
    liste_fichiers: Optional[List[str]] = None,
    motif_fichier: str = "*LL_Rougeole.xlsx",
    sheet_name: str = "LL_Rougeole",
    colonnes_attendues: Optional[List[str]] = None,
    sensible_a_la_casse: bool = False,
    colonne_source: Optional[str] = "Provenance"   # 🔹 peut être None
) -> pd.DataFrame:
    """
    Charge plusieurs fichiers Excel, nettoie les colonnes, ajoute une colonne source (optionnelle),
    détecte les doublons et fusionne les données.

    Cette fonction permet de compiler automatiquement plusieurs fichiers Excel d’une même structure 
    (p. ex. liste linéaire d’une maladie) en un seul DataFrame, avec des colonnes harmonisées. 
    Chaque ligne peut être enrichie d’une colonne indiquant la provenance (nom du fichier source ou autre).

    Args:
        dossier_racine (str, optionnel): Chemin vers un dossier contenant les fichiers Excel.
        liste_fichiers (List[str], optionnel): Liste de chemins de fichiers Excel à charger directement.
        motif_fichier (str): Motif de recherche des fichiers Excel dans le dossier 
            (par défaut "*LL_Rougeole.xlsx").
        sheet_name (str): Nom de la feuille Excel à lire (par défaut "LL_Rougeole").
        colonnes_attendues (List[str], optionnel): Liste des colonnes attendues dans les fichiers. 
            Si fournie, une vérification est effectuée après la fusion.
        sensible_a_la_casse (bool): Indique si la recherche des colonnes doit être sensible à la casse 
            (par défaut False).
        colonne_source (str | None): Nom de la colonne ajoutée pour indiquer la provenance des données.
            Si None, aucune colonne n’est ajoutée. (par défaut "Provenance").

    Returns:
        pd.DataFrame: DataFrame fusionné contenant toutes les données nettoyées.

    Raises:
        ValueError: Si aucun fichier valide n'est trouvé ou chargé.

    Exemple:
        >>> df1 = charger_fichiers_excel(
        ...     dossier_racine="Cholera",
        ...     motif_fichier="*_LL_Cholera*.xlsx",
        ...     sheet_name="LL_Cholera",
        ...     colonne_source="Fichier_origine"   # ajoute une colonne "Fichier_origine"
        ... )
        >>> df2 = charger_fichiers_excel(
        ...     dossier_racine="Cholera",
        ...     motif_fichier="*_LL_Cholera*.xlsx",
        ...     sheet_name="LL_Cholera",
        ...     colonne_source=None   # aucune colonne ajoutée
        ... )
    """
    if liste_fichiers is None:
        if dossier_racine is None:
            raise ValueError("Il faut fournir soit un dossier_racine, soit une liste_fichiers.")
        liste_fichiers = lister_fichiers_excel(
            dossier_racine, motif_fichier, sensible_a_la_casse
        )

    donnees_brutes = lire_fichiers_excel(
        liste_fichiers, sheet_name=sheet_name, sensible_a_la_casse=sensible_a_la_casse
    )

    dataframes = []
    for fichier, df in donnees_brutes.items():
        try:
            provenance = os.path.splitext(fichier)[0]
            df = clean_all_column_names(df)

            # 🔹 ajout de la colonne seulement si demandé
            if colonne_source is not None:
                df[colonne_source] = provenance

            detecter_doublons_standardises(df, provenance)
            dataframes.append(df)

        except Exception as e:
            logger.warning(f"Erreur lors du traitement de {fichier} : {e}")

    if not dataframes:
        raise ValueError("Aucun fichier valide n’a été chargé.")

    afficher_colonnes_standardisees(dataframes)
    df_fusionne = fusionner_colonnes_similaires(dataframes)

    if colonnes_attendues:
        verifier_colonnes(df_fusionne, [standardiser_nom(c) for c in colonnes_attendues])

    return df_fusionne

def exporter_dataframe_excel(df: pd.DataFrame, dossier: str, base_nom: str, sheet_name: str = "Feuille1") -> str:
    """
    Exporte un DataFrame en fichier Excel avec nom incluant la date et l'heure.
    
    Args:
        df (pd.DataFrame): Le DataFrame à exporter.
        dossier (str): Le dossier où enregistrer le fichier.
        base_nom (str): Le préfixe du nom de fichier (ex. "rdc_compilation_LL_Cholera").
        sheet_name (str): Nom de la feuille Excel (par défaut: "Feuille1").
    
    Returns:
        str: Le chemin complet du fichier exporté.
    """
    # Assure que le dossier existe
    os.makedirs(dossier, exist_ok=True)
    
    # Date + heure formatée : jour_mois_année_heure_minute_seconde
    horodatage = datetime.now().strftime("%d-%m-%Y_%H-%M-%S").replace("-", "_")
    
    # Construction du chemin complet
    nom_fichier = f"{base_nom}_{horodatage}.xlsx"
    chemin_complet = os.path.join(dossier, nom_fichier)

    # Export du DataFrame
    df.to_excel(chemin_complet, index=False, sheet_name=sheet_name)
    
    return chemin_complet

def fusionner_fichiers_homogenes(
    fichiers: List[Union[str, pd.DataFrame]],
    chemin_sortie: str = None,
    avec_source: bool = False,
    colonne_source: Optional[str] = "Provenance",
    reset_index: bool = True,
    colonnes_communes_only: bool = False,
    exporter: bool = False 
) -> pd.DataFrame:
    """
    Fusionne plusieurs fichiers (ou DataFrames) avec gestion automatique de la provenance.
    Si `exporter=True`, enregistre le résultat au format CSV/XLSX avec un horodatage.

    Args:
        fichiers (List[Union[str, pd.DataFrame]]): Chemins ou DataFrames à fusionner.
        chemin_sortie (str, optional): Chemin pour sauvegarder le résultat.
        avec_source (bool): Ajouter une colonne indiquant le fichier source.
        colonne_source (str | None): Nom de la colonne de provenance. Si None, aucune colonne n’est ajoutée.
        reset_index (bool): Réinitialiser l'index.
        colonnes_communes_only (bool): Si True, ne garde que les colonnes communes.
        exporter (bool): ✅ Si True, sauvegarde le fichier fusionné. Par défaut False.

    Returns:
        pd.DataFrame: DataFrame fusionné.
    """
    df_liste = []
    horodatage_str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

    for fichier in fichiers:
        if isinstance(fichier, pd.DataFrame):
            df = fichier.copy()
            nom_source = "DataFrame"
        elif isinstance(fichier, str):
            try:
                if not os.path.exists(fichier):
                    logger.error(f"[Fichier introuvable] {fichier}")
                    continue

                ext = os.path.splitext(fichier)[1].lower()
                if ext == ".csv":
                    df = pd.read_csv(fichier)
                elif ext in [".xls", ".xlsx"]:
                    df = pd.read_excel(fichier)
                else:
                    logger.warning(f"[Ignore] Format non supporté: {fichier}")
                    continue

                nom_source = os.path.basename(fichier)
            except Exception as e:
                logger.error(f"[Erreur lecture] {fichier} : {e}")
                continue
        else:
            logger.warning(f"[Ignore] Type non supporté : {type(fichier)}")
            continue

        # ✅ Gestion colonne source uniquement si demandé ET si colonne_source n’est pas None
        if avec_source and colonne_source is not None:
            colonnes_existantes = df.columns
            nouvelle_colonne = colonne_source

            if colonne_source in colonnes_existantes:
                i = 2
                while f"{colonne_source}_fusion_{i}" in colonnes_existantes:
                    i += 1
                nouvelle_colonne = f"{colonne_source}_fusion_{i}"

            df[nouvelle_colonne] = nom_source
            logger.info(f"[Provenance] Colonne '{nouvelle_colonne}' ajoutée avec valeur '{nom_source}'")

        df_liste.append(df)

    if not df_liste:
        raise ValueError("Aucun fichier valide n’a été chargé.")

    colonnes_bases = set(df_liste[0].columns)

    if colonnes_communes_only:
        for df in df_liste[1:]:
            colonnes_bases &= set(df.columns)

        if not colonnes_bases:
            raise ValueError("Aucune colonne commune entre les fichiers.")

        colonnes_utilisees = sorted(colonnes_bases)
        df_liste = [df[colonnes_utilisees].copy() for df in df_liste]
        logger.info(f"[Fusion - colonnes communes] Colonnes fusionnées : {colonnes_utilisees}")
    else:
        for i, df in enumerate(df_liste[1:], 1):
            if set(df.columns) != colonnes_bases:
                logger.error(f"[Colonnes divergentes] Fichier #{i} ne correspond pas.")
                raise ValueError("Tous les fichiers doivent avoir les mêmes colonnes. Utilisez 'colonnes_communes_only=True' pour forcer l'intersection.")
        colonnes_utilisees = sorted(colonnes_bases)
        logger.info(f"[Fusion - colonnes identiques] Colonnes fusionnées : {colonnes_utilisees}")

    df_final = pd.concat(df_liste, axis=0, ignore_index=reset_index)

    # ✅ Sauvegarde conditionnelle uniquement si exporter=True
    if exporter and chemin_sortie:
        base, ext = os.path.splitext(chemin_sortie)
        if horodatage_str not in base:
            chemin_sortie = f"{base}_{horodatage_str}{ext}"

        dossier = os.path.dirname(chemin_sortie)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier, exist_ok=True)

        try:
            if ext == ".csv":
                df_final.to_csv(chemin_sortie, index=False)
            elif ext in [".xls", ".xlsx"]:
                df_final.to_excel(chemin_sortie, index=False)
            else:
                logger.warning(f"[Sauvegarde ignorée] Format non supporté: {chemin_sortie}")
        except Exception as e:
            logger.error(f"[Erreur sauvegarde] {chemin_sortie} : {e}")
        else:
            logger.info(f"[Fichier sauvegardé] {chemin_sortie}")
    elif exporter:
        logger.warning("[Exporter=True] mais aucun chemin de sauvegarde fourni.")
    else:
        logger.info("[Fusion sans export] Résultat retourné uniquement en mémoire.")

    logger.info(f"[Fusion réussie] {len(df_liste)} fichiers fusionnés, total : {df_final.shape[0]} lignes.")
    return df_final

# Fonction charger fichier avec log
def log_colonnes(df_orig: pd.DataFrame, df_apres: pd.DataFrame, col_funcs: Optional[Dict[str, str]] = None, fichier: str = "") -> pd.DataFrame:
    col_funcs = col_funcs or {}
    rows = []
    for orig_col, after_col in zip(df_orig.columns, df_apres.columns):
        changed = standardiser_nom(orig_col) != after_col or col_funcs.get(after_col) is not None
        rows.append({
            "variable": after_col,
            "before": orig_col,
            "after": after_col,
            "changed": changed,
            "fonction_nettoyage": col_funcs.get(after_col),
            "fichier": fichier
        })
    return pd.DataFrame(rows)

def charger_fichiers_excel_avec_log(
        dossier_racine: Optional[str] = None,
        liste_fichiers: Optional[List[str]] = None,
        motif_fichier: str = "*LL_Cholera*.xlsx",
        sheet_name: str = "LL_Cholera",
        colonnes_attendues: Optional[List[str]] = None,
        sensible_a_la_casse: bool = False,
        colonne_source: Optional[str] = "Provenance",
        mapping_colonnes: Optional[str] = mapping_file_path,
        log_only_changed: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge tous les fichiers Excel (.xlsx) dans le dossier (et sous-dossiers), standardise,
    applique le mapping, ajoute une colonne source et retourne un log des colonnes modifiées.
    """
    # 🔹 Liste de fichiers
    if liste_fichiers is None:
        if dossier_racine is None:
            raise ValueError("Il faut fournir soit un dossier_racine, soit une liste de fichiers.")
        # 👉 Nouvelle fonction utilisée ici
        fichiers = lister_fichiers_excel(dossier_racine, motif_fichier, sensible_a_la_casse)
        if not fichiers:
            raise ValueError(f"Aucun fichier trouvé avec le motif {motif_fichier}")
    else:
        fichiers = [Path(f) for f in liste_fichiers]

    # 🔹 Mapping
    mapping_dict: Dict[str,str] = {}
    if mapping_colonnes and Path(mapping_colonnes).exists():
        mapping_df = pd.read_excel(mapping_colonnes)
        if 'Original' not in mapping_df.columns or 'Renamed' not in mapping_df.columns:
            raise ValueError("Le fichier de mapping doit contenir les colonnes 'Original' et 'Renamed'")
        mapping_dict = {
            standardiser_nom(str(k).strip() if pd.notna(k) else ""): str(v).strip()
            for k, v in zip(mapping_df['Original'], mapping_df['Renamed'])
            if pd.notna(v) and str(v).strip() != ""
        }

    dataframes = []
    logs = []

    for fichier in fichiers:
        try:
            df_orig = pd.read_excel(fichier, sheet_name=sheet_name)
            df = df_orig.copy()

            # Standardiser les noms de colonnes
            df.columns = [standardiser_nom(c) for c in df.columns]
            col_funcs = {c: "standardisation" for c in df.columns}

            # Appliquer le mapping si fourni
            if mapping_dict:
                cols_a_renommer = {c: mapping_dict[c] for c in df.columns if c in mapping_dict}
                df.rename(columns=cols_a_renommer, inplace=True)
                for c in cols_a_renommer.values():
                    col_funcs[c] = "renommage"

            # Ajouter colonne source si demandé
            if colonne_source:
                df[colonne_source] = fichier.stem
                col_funcs[colonne_source] = "ajout_colonne_source"

            # Log des colonnes
            df_log = log_colonnes(df_orig, df, col_funcs=col_funcs, fichier=fichier.name)
            logs.append(df_log)
            dataframes.append(df)
            logger.info(f"✅ Lu : {fichier.name} - feuille : {sheet_name}")

        except Exception as e:
            logger.warning(f"Erreur traitement {fichier.name} : {e}")

    if not dataframes:
        raise ValueError("Aucun fichier valide chargé.")

    # 🔹 Fusionner tous les DataFrames
    df_fusionne = pd.concat(dataframes, ignore_index=True)
    df_log_final = pd.concat(logs, ignore_index=True) if logs else pd.DataFrame()

    # 🔹 Vérifier colonnes attendues
    if colonnes_attendues:
        colonnes_standard = [standardiser_nom(c) for c in colonnes_attendues]
        colonnes_manquantes = set(colonnes_standard) - set(df_fusionne.columns)
        if colonnes_manquantes:
            logger.warning(f"Colonnes attendues manquantes : {colonnes_manquantes}")

    # 🔹 Filtrer log si demandé
    if log_only_changed:
        df_log_final = df_log_final[df_log_final['changed'] == True].reset_index(drop=True)

    return df_fusionne, df_log_final

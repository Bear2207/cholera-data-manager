# -*- coding: utf-8 -*-
import os
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, List, Tuple
import re

from dataminsante.compilation.fichiers_compilation import (
    charger_fichiers_excel_avec_log,
    exporter_dataframe_excel
)
from dataminsante.liste_lineaire.verification_renommage import (
    verifier_excel_recursive,
    creer_df_resume
)

# ================= Logger =================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

base_dir = Path(__file__).resolve().parents[2]
logs_dir = base_dir / "logs"
os.makedirs(logs_dir, exist_ok=True)
log_file = logs_dir / f"sop_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

mapping_file_path = base_dir / "data" / "Rename_columns.xlsx"

# ================= Étape 1 : Vérification =================
def verification_sop(
    dossier_racine: str,
    sheet_name: Optional[str] = None,
    mode: str = "tous",
    nom_feuille: Optional[str] = None,
    nomenclature: str = "sop",
    motif_fichier: Optional[str] = None,
    afficher: bool = False
) -> tuple[list[str], pd.DataFrame]:
    """
    Vérifie les fichiers Excel dans un dossier selon SOP ou Resume.
    Retourne :
        - liste des fichiers valides
        - DataFrame de détails (df_details)
    """

    if nomenclature.lower() not in ["sop", "resume"]:
        raise ValueError(f"nomenclature '{nomenclature}' non reconnue. Doit être 'sop' ou 'resume'.")

    feuille_a_verifier = sheet_name or nom_feuille

    # Appel de la fonction centrale de vérification
    rapport = verifier_excel_recursive(
        dossier=dossier_racine,
        nomenclature=nomenclature.lower(),
        mode=mode,
        nom_feuille=feuille_a_verifier,
        afficher=afficher
    )

    fichiers_valides = rapport["fichiers_valides"]

    # Filtrage sur motif_fichier si fourni
    if motif_fichier:
        motif_regex = motif_fichier.replace("*", ".*")
        regex = re.compile(motif_regex, re.IGNORECASE)
        fichiers_valides = [f for f in fichiers_valides if regex.fullmatch(os.path.basename(f))]

    # Comptage simple comme dans l'ancienne version
    logger.info(f"Fichiers valides : {len(fichiers_valides)} / {rapport['total_fichiers']}")

    df_resume, df_details = creer_df_resume(rapport)
    return fichiers_valides, df_details

# ================= Étape 2 : Chargement et nettoyage =================
def charger_et_nettoyer(
    fichiers: List[str],
    sheet_name: str,
    colonne_source: str = "Provenance",
    mapping_colonnes: Optional[str] = None,
    log_only_changed: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    if mapping_colonnes is None:
        mapping_colonnes = str(mapping_file_path)

    df_fusionne, df_log = charger_fichiers_excel_avec_log(
        liste_fichiers=fichiers,
        sheet_name=sheet_name,
        colonne_source=colonne_source,
        mapping_colonnes=mapping_colonnes,
        log_only_changed=log_only_changed
    )
    logger.info(f"DataFrame fusionné : {df_fusionne.shape[0]} lignes, {df_fusionne.shape[1]} colonnes")
    return df_fusionne, df_log

# ================= Étape 3 : Validation contenu =================
def verifier_contenu_sop(df: pd.DataFrame, colonnes_critique: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Vérifie les colonnes critiques dans le DataFrame.
    Si colonnes_critique=None, aucune vérification n'est faite.
    """
    df["valide_sop"] = True

    if colonnes_critique:
        for col in colonnes_critique:
            if col not in df.columns:
                logger.warning(f"Colonne critique absente : {col}")
                df["valide_sop"] = False
            else:
                missing = df[col].isna().sum()
                if missing > 0:
                    logger.warning(f"{missing} valeurs manquantes dans colonne {col}")
                    df["valide_sop"] = False

        total_invalides = (~df["valide_sop"]).sum()
        logger.info(f"Lignes invalides SOP : {total_invalides} / {len(df)}")

    return df


# ================= Étape 4 : Export =================
def exporter_sop(df: pd.DataFrame, df_log: pd.DataFrame, dossier_sortie: str, base_nom: str):
    os.makedirs(dossier_sortie, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    excel_sortie = exporter_dataframe_excel(df, dossier_sortie, f"{base_nom}_{timestamp}", sheet_name="Données")
    logger.info(f"DataFrame exporté : {excel_sortie}")

    log_sortie = exporter_dataframe_excel(df_log, dossier_sortie, f"{base_nom}_log_{timestamp}", sheet_name="Log")
    logger.info(f"Log exporté : {log_sortie}")

# ================= Pipeline complet =================
def pipeline_sop(
    dossier_racine: str,
    sheet_name: str,
    dossier_sortie: str,
    motif_fichier: Optional[str] = None,
    colonne_source: str = "Provenance",
    nomenclature: str = "sop",
    mode: str = "tous",
    mapping_colonnes: Optional[str] = mapping_file_path,
    colonnes_critique: Optional[List[str]] = None
) -> dict:
    """
    Pipeline complet pour SOP ou Resume :
    - Vérifie les fichiers via verification_sop
    - Charge et nettoie les données
    - Vérifie les colonnes critiques
    - Exporte résultats et logs
    """

    fichiers_valides, df_details = verification_sop(
        dossier_racine=dossier_racine,
        sheet_name=sheet_name,
        mode=mode,
        motif_fichier=motif_fichier,
        nomenclature=nomenclature
    )

    if not fichiers_valides:
        logger.error(f"Aucun fichier valide pour le pipeline {nomenclature.upper()}.")
        return {}

    df_fusionne, df_log = charger_et_nettoyer(
        fichiers=fichiers_valides,
        sheet_name=sheet_name,
        colonne_source=colonne_source,
        mapping_colonnes=mapping_colonnes
    )

    df_fusionne = verifier_contenu_sop(df_fusionne, colonnes_critique=colonnes_critique)

    exporter_sop(df_fusionne, df_log, dossier_sortie, base_nom=f"pipeline_{nomenclature}")

    logger.info(f"Pipeline {nomenclature.upper()} terminé avec succès.")

    return {
        "df_fusionne": df_fusionne,
        "df_log": df_log,
        "df_resume": df_details,
        "fichiers_valides": fichiers_valides
    }

# Renommer un ou plusieurs fichier
def renommer_excel_sop(
    dossier: str,
    type_fichier: str = None,
    critere: str = r"(?<!_compiled)\.xlsx$",
    remplacement: str = "_compiled.xlsx",
    log_file: str = "renommage_log.xlsx"
):
    """
    Renomme les fichiers Excel selon le SOP Cholera et logge les changements.

    Args:
        dossier (str): chemin du dossier racine
        type_fichier (str, optional): filtrer par type de fichier (LLCholera, BDContactsCholera...)
        critere (str): motif regex à chercher dans le nom des fichiers
        remplacement (str): texte de remplacement pour le critère trouvé
        log_file (str): fichier Excel pour enregistrer le log
    """
    dossier_path = Path(dossier)
    fichiers_excel = dossier_path.rglob("*.xlsx")
    log = []

    for f in fichiers_excel:
        nom_initial = f.name

        # Filtrer par type de fichier si demandé
        if type_fichier and not nom_initial.startswith(type_fichier):
            continue

        if re.search(critere, nom_initial):
            nouveau_nom = re.sub(critere, remplacement, nom_initial)
            chemin_nouveau = f.with_name(nouveau_nom)

            # Gérer les conflits
            if chemin_nouveau.exists():
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                chemin_nouveau = f.with_name(f"{nouveau_nom.stem}_{timestamp}.xlsx")

            f.rename(chemin_nouveau)

            log.append({
                "chemin_origine": str(f),
                "nom_origine": nom_initial,
                "nom_nouveau": chemin_nouveau.name,
                "chemin_nouveau": str(chemin_nouveau),
                "type_fichier": type_fichier if type_fichier else "tous",
                "date_renommage": datetime.now()
            })

            logging.warning(f"Renommé : {nom_initial} → {chemin_nouveau.name}")

    if log:
        df_log = pd.DataFrame(log)
        df_log.to_excel(Path(dossier) / log_file, index=False)
        logging.info(f"Log sauvegardé : {log_file}")
    else:
        logging.warning("Aucun fichier ne correspond au critère.")
"""Chargement et fusion des fichiers Excel.
Utilise les fonctions `dataminsante` existantes pour rester compatible.
"""
from typing import Tuple
import pandas as pd
from dataminsante.compilation import charger_fichiers_excel, generer_nom_fichier_excel
from pathlib import Path
from config import INPUT_DIR, MOTIF_FICHIER, NOM_FEUILLE


def creer_resume(dossier: str = INPUT_DIR, nom_feuille: str = NOM_FEUILLE, afficher: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Parcourt les fichiers Excel et crée un résumé (wrapper)."""
    resume = verifier_excel_recursive(dossier, nomenclature="resume", mode="tous", nom_feuille=nom_feuille, afficher=afficher, detecter_header=True)
    df_resume, df_details = creer_df_resume(resume)
    return df_resume, df_details


def charger_et_fusionner(dossier_racine: str = INPUT_DIR, motif_fichier: str = MOTIF_FICHIER, sheet_name: str = NOM_FEUILLE, colonne_source: str | None = "Provenance") -> pd.DataFrame:
    """Charge et fusionne les fichiers Excel en utilisant dataminsante.compilation.charger_fichiers_excel.
    Retourne un DataFrame fusionné.
    """
    df = charger_fichiers_excel(
        dossier_racine=dossier_racine,
        motif_fichier=motif_fichier,
        sheet_name=sheet_name,
        colonne_source=colonne_source
    )
    return df


def charger_et_fusionner_avec_log(dossier_racine: str = INPUT_DIR, motif_fichier: str = MOTIF_FICHIER, sheet_name: str = NOM_FEUILLE, colonne_source: str | None = "Provenance") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Idem mais retourne aussi le log si disponible."""
    df, df_log = charger_fichiers_excel_avec_log(
        dossier_racine=dossier_racine,
        motif_fichier=motif_fichier,
        sheet_name=sheet_name,
        colonne_source=colonne_source
    )
    return df, df_log
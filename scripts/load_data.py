#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os
from utils import setup_logging, validate_dataframe

logger = setup_logging()

def load_raw_data(dossier_donnees, motif_fichier, nom_feuille):
    """
    Charger les données brutes depuis les fichiers Excel
    """
    logger.info(f"Chargement des données depuis: {dossier_donnees}")
    
    try:
        # Vérification préliminaire des fichiers
        resume = verifier_excel_recursive(
            dossier_donnees, 
            nomenclature="resume",
            mode="tous", 
            nom_feuille=nom_feuille, 
            afficher=False,
            detecter_header=True
        )
        
        df_resume, df_details = creer_df_resume(resume)
        logger.info(f"Résumé des fichiers: {len(df_resume)} fichiers trouvés")
        
        # Chargement des données
        df_compilation = charger_fichiers_excel(
            dossier_racine=dossier_donnees,
            motif_fichier=motif_fichier,
            sheet_name=nom_feuille,
            colonne_source="Provenance"
        )
        
        if validate_dataframe(df_compilation, "load_raw_data"):
            logger.info(f"Données brutes chargées: {len(df_compilation)} lignes")
            return df_compilation, df_resume, df_details
        else:
            raise ValueError("Échec du chargement des données brutes")
            
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        raise

def load_compiled_data(dossier_donnees, motif_fichier, nom_feuille):
    """
    Charger les données déjà compilées
    """
    logger.info("Chargement des données compilées")
    
    try:
        df_clean = charger_fichiers_excel(
            dossier_racine=dossier_donnees,
            motif_fichier=motif_fichier,
            sheet_name=nom_feuille,
            colonne_source=None
        )
        
        # Nettoyage des noms de colonnes
        df_clean = clean_all_column_names(df_clean)
        
        if validate_dataframe(df_clean, "load_compiled_data"):
            logger.info(f"Données compilées chargées: {len(df_clean)} lignes")
            return df_clean
        else:
            raise ValueError("Échec du chargement des données compilées")
            
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données compilées: {str(e)}")
        raise
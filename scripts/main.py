#!/usr/bin/env python
# coding: utf-8

"""
Script principal pour le pipeline de données Cholera
"""

import sys
import os

# Ajouter le chemin des scripts
sys.path.append(os.path.dirname(__file__))

from load_data import load_raw_data, load_compiled_data
from clean_data import (
    preprocess_columns, merge_similar_columns, clean_dates,
    clean_demographic_data, clean_geographic_data, 
    clean_categorical_data, replace_specific_values
)
from transform_data import (
    handle_duplicates, classify_cases, add_epidemiological_columns,
    finalize_data_cleaning, prepare_analysis_data
)
from export_data import (
    export_to_excel, export_to_csv, export_to_postgresql,
    generate_completeness_report
)
from utils import setup_logging, get_current_epi_week

def main():
    """
    Fonction principale du pipeline Cholera
    """
    logger = setup_logging()
    logger.info("Démarrage du pipeline Cholera")
    
    try:
        # Configuration
        DOSSIER_DONNEES = "/app/data/cholera"
        MOTIF_FICHIER = "*_LL_Cholera_*.xlsx"
        NOM_FEUILLE = "LL_Cholera"
        
        # Étape 1: Chargement des données
        logger.info("=== ÉTAPE 1: CHARGEMENT DES DONNÉES ===")
        df_raw, df_resume, df_details = load_raw_data(
            DOSSIER_DONNEES, MOTIF_FICHIER, NOM_FEUILLE
        )
        
        # Étape 2: Nettoyage des données
        logger.info("=== ÉTAPE 2: NETTOYAGE DES DONNÉES ===")
        df_processed = preprocess_columns(df_raw)
        df_merged = merge_similar_columns(df_processed)
        df_dates_cleaned = clean_dates(df_merged)
        df_demo_cleaned = clean_demographic_data(df_dates_cleaned)
        df_geo_cleaned = clean_geographic_data(df_demo_cleaned)
        df_cat_cleaned = clean_categorical_data(df_geo_cleaned)
        df_values_replaced = replace_specific_values(df_cat_cleaned)
        
        # Étape 3: Transformation des données
        logger.info("=== ÉTAPE 3: TRANSFORMATION DES DONNÉES ===")
        df_no_duplicates = handle_duplicates(df_values_replaced)
        df_classified = classify_cases(df_no_duplicates)
        df_epi = add_epidemiological_columns(df_classified)
        df_final = finalize_data_cleaning(df_epi)
        
        # Étape 4: Préparation pour l'analyse
        logger.info("=== ÉTAPE 4: PRÉPARATION POUR L'ANALYSE ===")
        semaine_epi_max = get_current_epi_week()
        df_analysis = prepare_analysis_data(df_final, 1, semaine_epi_max)
        
        # Étape 5: Export des données
        logger.info("=== ÉTAPE 5: EXPORT DES DONNÉES ===")
        
        # Export Excel
        excel_path = export_to_excel(
            df_analysis, 
            base_nom=f"rdc_compilation_LL_Cholera_SE01_SE{semaine_epi_max}"
        )
        
        # Export CSV
        csv_path = export_to_csv(
            df_analysis,
            base_nom=f"cholera_data_se01_se{semaine_epi_max}"
        )
        
        # Export PostgreSQL
        export_to_postgresql(df_analysis, "cholera_cases_clean")
        
        # Rapport de complétude
        df_comp, df_resume_comp = generate_completeness_report(df_analysis)
        
        logger.info("=== PIPELINE TERMINÉ AVEC SUCCÈS ===")
        logger.info(f"Données exportées: {len(df_analysis)} cas")
        logger.info(f"Fichier Excel: {excel_path}")
        logger.info(f"Fichier CSV: {csv_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du pipeline: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
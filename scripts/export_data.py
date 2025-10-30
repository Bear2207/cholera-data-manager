#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os
from sqlalchemy import create_engine
from utils import setup_logging

logger = setup_logging()

def export_to_excel(df, dossier="output", base_nom=None, sheet_name="LL_Cholera"):
    """
    Exporter le DataFrame vers Excel
    """
    logger.info("Export vers Excel")
    
    if base_nom is None:
        base_nom = f"rdc_compilation_LL_Cholera_SE01_SE41"
    
    try:
        chemin_export = exporter_dataframe_excel(
            df=df,
            dossier=dossier,
            base_nom=base_nom,
            sheet_name=sheet_name
        )
        
        logger.info(f"Export Excel réussi: {chemin_export}")
        return chemin_export
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export Excel: {str(e)}")
        raise

def export_to_csv(df, dossier="output", base_nom=None):
    """
    Exporter le DataFrame vers CSV pour PostgreSQL
    """
    logger.info("Export vers CSV")
    
    if base_nom is None:
        base_nom = "cholera_data_clean"
    
    try:
        # S'assurer que le dossier existe
        os.makedirs(dossier, exist_ok=True)
        
        chemin_csv = os.path.join(dossier, f"{base_nom}.csv")
        
        # Exporter en CSV
        df.to_csv(chemin_csv, index=False, encoding='utf-8')
        
        logger.info(f"Export CSV réussi: {chemin_csv}")
        return chemin_csv
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export CSV: {str(e)}")
        raise

def export_to_postgresql(df, table_name="cholera_cases"):
    """
    Exporter le DataFrame vers PostgreSQL
    """
    logger.info(f"Export vers PostgreSQL - table: {table_name}")
    
    try:
        # Configuration de la connexion
        db_config = {
            'host': 'postgres',
            'port': '5432',
            'database': 'll_cousp',
            'user': 'bearing',
            'password': 'Couspdata'
        }
        
        # Créer la connexion
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Exporter vers PostgreSQL
        df.to_sql(
            table_name,
            engine,
            if_exists='replace',
            index=False,
            method='multi'
        )
        
        logger.info(f"Export PostgreSQL réussi: {len(df)} lignes insérées")
        
        # Fermer la connexion
        engine.dispose()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export PostgreSQL: {str(e)}")
        raise

def generate_completeness_report(df):
    """
    Générer un rapport de complétude des données
    """
    logger.info("Génération du rapport de complétude")
    
    from dataminsante.colonne_valeur.valeurs_completude import *
    
    # Liste des provinces attendues
    provinces_cholera = [
        "Equateur", "Kasai Central", "Kasai Oriental", "Kinshasa", 
        "Kongo Central", "Kwilu", "Lomami", "Maindombe", "Maniema", 
        "Mongala", "Nord Kivu", "Sud Kivu", "Tanganyika", "Tshopo", "Tshuapa"
    ]
    
    # Provinces présentes dans les données
    provinces_compile_cholera = df["Province_notification"].unique()
    
    # Comparaison normalisée
    resultat_listes = comparer_listes(provinces_cholera, provinces_compile_cholera)
    resultat_calcul = calculer_completude(provinces_cholera, provinces_compile_cholera)
    
    # Créer un DataFrame pour visualiser les résultats
    df_comparaison = pd.DataFrame({
        "Provinces attendues": provinces_cholera,
        "Présentes": [p in provinces_compile_cholera for p in provinces_cholera],
        "Manquantes": [p if p not in provinces_compile_cholera else "" for p in provinces_cholera]
    })
    
    # Résumé global
    df_resume_completude = pd.DataFrame({
        "Total provinces attendues": [resultat_calcul["nb_attendus"]],
        "Provinces trouvées": [resultat_calcul["nb_reçus"]],
        "Complétude (%)": [resultat_calcul["completude_%"]],
        "Provinces manquantes": [", ".join(resultat_calcul["manquantes"])]
    })
    
    logger.info(f"Complétude des provinces: {resultat_calcul['completude_%']}%")
    
    return df_comparaison, df_resume_completude
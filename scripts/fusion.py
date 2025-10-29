#!/usr/bin/env python3
"""
Étape 2: Fusion des colonnes similaires et restructuration
"""

import pandas as pd
import numpy as np
from scripts.config import *
from scripts.utils import *

def filtrer_et_reorganiser_colonnes(df):
    """Filtre et réorganise les colonnes selon le standard Cholera"""
    logger("Filtrage et réorganisation des colonnes...")
    
    # Colonnes existantes à garder
    colonnes_existantes = [col for col in COLONNES_CHOLERA if col in df.columns]
    colonnes_manquantes = [col for col in COLONNES_CHOLERA if col not in df.columns]
    
    logger(f"Colonnes à conserver: {len(colonnes_existantes)}")
    logger(f"Colonnes manquantes: {len(colonnes_manquantes)}")
    
    # Créer un nouveau dataframe avec les colonnes dans l'ordre
    df_filtre = pd.DataFrame()
    
    for col in COLONNES_CHOLERA:
        if col in df.columns:
            df_filtre[col] = df[col]
        else:
            df_filtre[col] = np.nan
            logger(f"Colonne ajoutée (vide): {col}", "warning")
    
    return df_filtre

def fusionner_colonnes_similaires(df):
    """Fusionne les colonnes similaires"""
    logger("Fusion des colonnes similaires...")
    
    df_fusion = df.copy()
    
    for nouvelle_col, anciennes_cols in GROUPES_COLONNES_FUSION.items():
        cols_existantes = [col for col in anciennes_cols if col in df_fusion.columns]
        
        if len(cols_existantes) > 1:
            logger(f"Fusion: {cols_existantes} → {nouvelle_col}")
            
            # Fusionner les colonnes (première valeur non-nulle)
            valeurs_fusionnees = []
            for idx in range(len(df_fusion)):
                valeurs_ligne = [df_fusion.at[idx, col] for col in cols_existantes 
                               if pd.notna(df_fusion.at[idx, col])]
                valeurs_fusionnees.append(valeurs_ligne[0] if valeurs_ligne else np.nan)
            
            df_fusion[nouvelle_col] = valeurs_fusionnees
            
            # Supprimer les anciennes colonnes
            for col in cols_existantes:
                if col != nouvelle_col:
                    del df_fusion[col]
    
    return df_fusion

def executer_fusion():
    """Exécute l'étape de fusion"""
    logger("=== ÉTAPE 2: FUSION DES COLONNES ===")
    
    # Charger les données compilées
    df_compile = charger_etape_precedente(COMPILED_DIR, "01_donnees_compilees", 'parquet')
    
    # Filtrer et réorganiser les colonnes
    df_filtre = filtrer_et_reorganiser_colonnes(df_compile)
    
    # Fusionner les colonnes similaires
    df_fusion = fusionner_colonnes_similaires(df_filtre)
    
    # Sauvegarder l'étape
    chemin_sauvegarde = sauvegarder_etape(
        df_fusion, 
        FUSED_DIR, 
        "02_donnees_fusionnees", 
        'parquet'
    )
    
    # Générer le rapport
    generer_rapport_etape(df_fusion, "Fusion")
    
    return df_fusion, chemin_sauvegarde

def main():
    """Fonction principale de fusion"""
    try:
        df_fusion, chemin = executer_fusion()
        logger(f"Fusion terminée: {chemin}", "success")
        return df_fusion, chemin
    except Exception as e:
        logger(f"Erreur lors de la fusion: {e}", "error")
        raise

if __name__ == "__main__":
    main()
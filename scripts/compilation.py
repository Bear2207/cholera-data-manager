#!/usr/bin/env python3
"""
Étape 1: Compilation des fichiers Excel bruts
"""

import pandas as pd
import glob
import os
from scripts.config import *
from scripts.utils import *

def compiler_fichiers_excel():
    """Charge et fusionne tous les fichiers Excel bruts"""
    logger("=== ÉTAPE 1: COMPILATION DES FICHIERS EXCEL ===")
    
    # Vérifier les fichiers
    fichiers = verifier_fichiers_excel(CONFIG['dossier_donnees'], CONFIG['motif_fichier'])
    
    dataframes = []
    for fichier in fichiers:
        try:
            df = pd.read_excel(fichier, sheet_name=CONFIG['nom_feuille'])
            # Ajouter la provenance si elle n'existe pas
            if 'provenance' not in df.columns:
                df['provenance'] = os.path.basename(fichier)
            dataframes.append(df)
            logger(f"Chargé: {os.path.basename(fichier)} - {len(df)} lignes")
        except Exception as e:
            logger(f"Erreur avec {os.path.basename(fichier)}: {e}", "error")
    
    if not dataframes:
        raise ValueError("Aucun fichier n'a pu être chargé")
    
    # Fusionner tous les dataframes
    df_fusionne = pd.concat(dataframes, ignore_index=True)
    logger(f"Données fusionnées: {len(df_fusionne)} lignes, {len(df_fusionne.columns)} colonnes")
    
    # Nettoyer les noms de colonnes
    df_fusionne.columns = [nettoyer_nom_colonne(col) for col in df_fusionne.columns]
    logger(f"Colonnes après nettoyage: {len(df_fusionne.columns)}")
    
    # Sauvegarder l'étape
    chemin_sauvegarde = sauvegarder_etape(
        df_fusionne, 
        COMPILED_DIR, 
        "01_donnees_compilees", 
        'parquet'
    )
    
    # Générer le rapport
    generer_rapport_etape(df_fusionne, "Compilation")
    
    return df_fusionne, chemin_sauvegarde

def main():
    """Fonction principale de compilation"""
    try:
        df_compile, chemin = compiler_fichiers_excel()
        logger(f"Compilation terminée: {chemin}", "success")
        return df_compile, chemin
    except Exception as e:
        logger(f"Erreur lors de la compilation: {e}", "error")
        raise

if __name__ == "__main__":
    main()
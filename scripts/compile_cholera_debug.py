#!/usr/bin/env python3
"""
Script de compilation, fusion et nettoyage des données Cholera
Version debug pour identifier les problèmes de chargement
"""

import pandas as pd
import numpy as np
import os
import re
import glob
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration des chemins pour Docker
BASE_DIR = Path("/app")  # Chemin absolu dans le conteneur
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "cholera"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
DB_DATA_DIR = BASE_DIR / "db" / "data"

# Création des dossiers
for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_OUTPUTS_DIR, DB_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Paramètres configurables
CONFIG = {
    'dossier_donnees': DATA_RAW_DIR,
    'motif_fichier': "*.xlsx",  # Pattern plus large pour debug
    'dossier_sortie': DATA_OUTPUTS_DIR,
    'dossier_csv': DB_DATA_DIR,
    'annee_filtre': 2025
}

def logger(message, type="info"):
    """Journalisation des messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "info": "ℹ️",
        "success": "✅", 
        "warning": "⚠️",
        "error": "❌"
    }.get(type, "ℹ️")
    
    print(f"{timestamp} {prefix} {message}")

def verifier_structure_dossiers():
    """Vérifie la structure des dossiers et fichiers"""
    logger("=== VÉRIFICATION DE LA STRUCTURE ===")
    
    logger(f"BASE_DIR: {BASE_DIR}")
    logger(f"DATA_RAW_DIR: {DATA_RAW_DIR}")
    logger(f"DATA_RAW_DIR existe: {DATA_RAW_DIR.exists()}")
    
    # Lister tous les fichiers dans le dossier raw
    if DATA_RAW_DIR.exists():
        tous_les_fichiers = list(DATA_RAW_DIR.glob("*"))
        logger(f"Fichiers trouvés dans {DATA_RAW_DIR}: {len(tous_les_fichiers)}")
        for f in tous_les_fichiers:
            logger(f"  - {f.name} (taille: {f.stat().st_size if f.is_file() else 'dossier'})")
    else:
        logger("❌ Le dossier DATA_RAW_DIR n'existe pas!", "error")
    
    # Vérifier les fichiers Excel spécifiques
    pattern = DATA_RAW_DIR / "*.xlsx"
    fichiers_excel = glob.glob(str(pattern))
    logger(f"Fichiers Excel trouvés avec pattern {pattern}: {len(fichiers_excel)}")
    for f in fichiers_excel:
        logger(f"  - {os.path.basename(f)}")

def analyser_fichier_excel(fichier_path):
    """Analyse un fichier Excel en détail"""
    logger(f"=== ANALYSE DU FICHIER: {os.path.basename(fichier_path)} ===")
    
    try:
        # Lire le fichier Excel
        xl = pd.ExcelFile(fichier_path, engine='openpyxl')
        logger(f"Feuilles disponibles: {xl.sheet_names}")
        
        # Analyser chaque feuille
        for sheet_name in xl.sheet_names:
            logger(f"--- Feuille: {sheet_name} ---")
            
            # Lire les premières lignes
            try:
                df_sample = pd.read_excel(fichier_path, sheet_name=sheet_name, nrows=5)
                logger(f"  Shape: {df_sample.shape}")
                logger(f"  Colonnes: {list(df_sample.columns)}")
                
                # Afficher les premières données
                if not df_sample.empty:
                    logger(f"  Premières données:")
                    for i, row in df_sample.head(2).iterrows():
                        logger(f"    Ligne {i}: {row.to_dict()}")
                
            except Exception as e:
                logger(f"  ❌ Erreur lecture feuille {sheet_name}: {e}", "error")
                
    except Exception as e:
        logger(f"❌ Erreur analyse fichier {fichier_path}: {e}", "error")

def charger_fichiers_excel_debug():
    """Charge les fichiers Excel avec debug détaillé"""
    logger("=== CHARGEMENT DES FICHIERS EXCEL ===")
    
    # Pattern plus large pour trouver tous les fichiers Excel
    pattern = str(DATA_RAW_DIR / "*.xlsx")
    fichiers = glob.glob(pattern)
    
    if not fichiers:
        logger(f"❌ AUCUN FICHIER TROUVÉ avec le pattern: {pattern}", "error")
        # Essayer d'autres patterns
        patterns_alternatifs = [
            DATA_RAW_DIR / "*.xls",
            DATA_RAW_DIR / "*.XLSX", 
            DATA_RAW_DIR / "*.XLS"
        ]
        for pat in patterns_alternatifs:
            fichiers_alt = glob.glob(str(pat))
            if fichiers_alt:
                logger(f"✅ Fichiers trouvés avec {pat}: {len(fichiers_alt)}")
                fichiers.extend(fichiers_alt)
    
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier Excel trouvé dans {DATA_RAW_DIR}")
    
    logger(f"Fichiers à charger: {len(fichiers)}")
    for f in fichiers:
        logger(f"  - {os.path.basename(f)}")
    
    all_dataframes = []
    
    for fichier in fichiers:
        try:
            logger(f"--- Chargement: {os.path.basename(fichier)} ---")
            
            # Analyser d'abord le fichier
            analyser_fichier_excel(fichier)
            
            # Essayer de lire avec différentes feuilles
            feuilles_essayer = ["LL_Cholera", "Feuille1", "Sheet1", "Data", 0]
            
            for feuille in feuilles_essayer:
                try:
                    logger(f"  Essai feuille: {feuille}")
                    df = pd.read_excel(
                        fichier, 
                        sheet_name=feuille,
                        engine='openpyxl',
                        dtype=str  # Lire tout en string d'abord
                    )
                    
                    if not df.empty:
                        logger(f"  ✅ SUCCÈS avec feuille {feuille}: {df.shape}")
                        
                        # Ajouter la provenance
                        df['provenance'] = os.path.basename(fichier)
                        
                        # Nettoyer les noms de colonnes
                        df = nettoyer_noms_colonnes(df)
                        
                        all_dataframes.append(df)
                        break  # Passer au fichier suivant
                    else:
                        logger(f"  ⚠️  Feuille {feuille} vide")
                        
                except Exception as e:
                    logger(f"  ❌ Échec feuille {feuille}: {e}")
            
            else:
                logger(f"  ❌ Aucune feuille valide trouvée dans {os.path.basename(fichier)}")
                
        except Exception as e:
            logger(f"❌ Erreur chargement {os.path.basename(fichier)}: {e}", "error")
    
    if not all_dataframes:
        raise Exception("Aucun dataframe n'a pu être chargé depuis les fichiers Excel")
    
    # Fusionner tous les dataframes
    logger("Fusion des dataframes...")
    try:
        df_fusionne = pd.concat(all_dataframes, ignore_index=True, sort=False)
        logger(f"✅ Fusion réussie: {df_fusionne.shape}")
        return df_fusionne
        
    except Exception as e:
        logger(f"❌ Erreur fusion: {e}", "error")
        raise

def nettoyer_noms_colonnes(df):
    """Nettoie les noms de colonnes"""
    logger("Nettoyage des noms de colonnes...")
    
    def clean_column_name(name):
        if pd.isna(name):
            return "colonne_inconnue"
        name = str(name).strip()
        name = re.sub(r'[^\w\s]', '_', name)
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'_+', '_', name)
        return name.lower().strip('_')
    
    new_columns = []
    for col in df.columns:
        new_col = clean_column_name(col)
        # Gérer les doublons
        counter = 1
        original_col = new_col
        while new_col in new_columns:
            new_col = f"{original_col}_{counter}"
            counter += 1
        new_columns.append(new_col)
    
    df.columns = new_columns
    logger(f"Colonnes après nettoyage: {len(df.columns)}")
    logger(f"Exemple colonnes: {list(df.columns[:5])}")
    
    return df

def main_debug():
    """Fonction principale de debug"""
    logger("=== DÉMARRAGE DU DEBUG CHOLERA ===")
    
    try:
        # Étape 1: Vérifier la structure
        verifier_structure_dossiers()
        
        # Étape 2: Charger les données avec debug
        df = charger_fichiers_excel_debug()
        
        if df.empty:
            logger("❌ Le dataframe est VIDE après chargement!", "error")
            return None
        
        logger(f"✅ Données chargées: {df.shape}")
        logger(f"Colonnes: {list(df.columns)}")
        
        # Sauvegarder les données brutes pour inspection
        output_debug = DATA_OUTPUTS_DIR / "debug_data_raw.csv"
        df.to_csv(output_debug, index=False, encoding='utf-8')
        logger(f"💾 Données brutes sauvegardées: {output_debug}")
        
        # Afficher un échantillon
        logger("=== ÉCHANTILLON DES DONNÉES ===")
        logger(f"Premières lignes:")
        print(df.head(3).to_string())
        
        logger("=== STATISTIQUES BRUTES ===")
        logger(f"Nombre total de lignes: {len(df)}")
        logger(f"Nombre de colonnes: {len(df.columns)}")
        
        # Vérifier les valeurs non nulles
        for col in df.columns[:10]:  # Premières 10 colonnes
            non_nulls = df[col].notna().sum()
            logger(f"  {col}: {non_nulls} valeurs non nulles")
        
        return df
        
    except Exception as e:
        logger(f"❌ Erreur critique: {e}", "error")
        import traceback
        logger(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    df_result = main_debug()
    
    if df_result is not None and not df_result.empty:
        logger("🎉 DEBUG TERMINÉ AVEC SUCCÈS!", "success")
    else:
        logger("💥 DEBUG ÉCHOUÉ - AUCUNE DONNÉE", "error")
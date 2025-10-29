#!/usr/bin/env python3
"""
Script de compilation, fusion et nettoyage des données Cholera
Version corrigée basée sur l'analyse des fichiers
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
BASE_DIR = Path("/app")
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
    'motif_fichier': "*.xlsx",
    'dossier_sortie': DATA_OUTPUTS_DIR,
    'dossier_csv': DB_DATA_DIR,
    'annee_filtre': 2025  # Mais on va désactiver le filtrage temporel pour l'instant
}

# Mapping des colonnes brutes vers les colonnes standard
COLUMN_MAPPING = {
    'id_prov_zs_structure_ann_num': 'n_epid_prov',
    'n_epi_rdc_pro_zs_as_ann_num': 'n_epid',
    'date_d_admission': 'date_admission', 
    'date_du_début_de_la_maladie': 'date_debut_maladie',
    'sem_epi': 'num_semaine_epi',
    'noms': 'nom_complet',
    'sexe_m_f': 'sexe',
    'age_en_année': 'age_annee',
    'age_en_mois_0_59mois': 'age_mois',
    'profession': 'profession',
    'province_de_provenance': 'province_provenance',
    'zone_de_santé_de_provenance': 'zone_de_sante_provenance',
    'aire_de_santé_de_provenance': 'aire_de_sante_provenance',
    'symptômes': 'symptomes',
    "prise_d_antibiotique_avant_l_admission_oui_non": 'prise_antibiotique_avant_admission',
    "nom_de_l_antibiotique": 'nom_antibiotique',
    'antécédents_morbides_diabète_hta_vih': 'antecedents_morbides',
    'femmes_enceintes_oui_non': 'femme_enceinte',
    'dégré_de_déshydratation': 'degre_deshydratation',
    'hospitalisation_oui_non': 'hospitalisation',
    'prélevement_oui_non': 'prelevement',
    'date_de_prélevement': 'date_prelevement',
    'tdr_realise_oui_non': 'tdr_realise',
    'nom_de_la_structure_realisant_le_tdr': 'nom_structure_realisant_le_tdr',
    'résultat_tdr_vco1_vco139_négatif': 'tdr_resultat',
    'résultat_labo': 'resultat_labo',
    'sérotype_ogawa_inaba': 'serotype',
    'traitement_antibiotique': 'traitement_antibiotique',
    'quantité_total_ringer_recue': 'quantite_total_ringer_recue',
    'quantité_total_sro_recue': 'quantite_total_sro_recue',
    'nom_du_ctc_utc': 'ctc_utc',
    'issue_décédé_transféré_gueri_evade': 'issue',
    'date_de_sortie': 'date_de_sortie_malade',
    'statut_vaccinal_vacciné_non_vacciné': 'statut_vaccinal',
    'nombre_de_dose_1_2': 'nombre_dose',
    'annee_de_vaccination': 'annee_vaccination',
    'source_éventuelle_de_contamination': 'source_eventuelle_de_contamination',
    "source_d_approvisionnement_en_eau": 'source_approvisionnement_en_eau',
    'observation': 'observation'
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

def charger_fichiers_excel():
    """Charge et fusionne tous les fichiers Excel"""
    logger("Chargement et fusion des fichiers Excel...")

    pattern = str(DATA_RAW_DIR / "*.xlsx")
    fichiers = glob.glob(pattern)
    
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier trouvé avec le pattern: {pattern}")
    
    logger(f"Fichiers trouvés: {len(fichiers)}")
    
    all_dataframes = []
    
    for fichier in fichiers:
        try:
            logger(f"Lecture de {os.path.basename(fichier)}")
            
            # Lire le fichier Excel
            df = pd.read_excel(
                fichier, 
                sheet_name="LL_Cholera",
                engine='openpyxl',
                dtype=str  # Lire tout en string d'abord
            )
            
            # Ajouter la provenance
            df['provenance'] = os.path.basename(fichier)
            
            # Nettoyer les noms de colonnes
            df = nettoyer_noms_colonnes(df)
            
            logger(f"✅ {os.path.basename(fichier)}: {df.shape}")
            all_dataframes.append(df)
            
        except Exception as e:
            logger(f"❌ Erreur avec {os.path.basename(fichier)}: {str(e)}", "error")
    
    if not all_dataframes:
        raise Exception("Aucun dataframe n'a pu être chargé")
    
    # Fusionner tous les dataframes
    logger("Fusion des dataframes...")
    df_fusionne = pd.concat(all_dataframes, ignore_index=True, sort=False)
    logger(f"✅ Fusion réussie: {df_fusionne.shape}")
    
    return df_fusionne

def nettoyer_noms_colonnes(df):
    """Nettoie les noms de colonnes"""
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
        counter = 1
        original_col = new_col
        while new_col in new_columns:
            new_col = f"{original_col}_{counter}"
            counter += 1
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df

def mapper_vers_standard(df):
    """Mappe les colonnes brutes vers le standard Cholera"""
    logger("Mapping des colonnes vers le standard...")
    
    df_standard = df.copy()
    
    # Créer un nouveau dataframe avec les colonnes standardisées
    for col_standard, col_brute in COLUMN_MAPPING.items():
        if col_brute in df_standard.columns:
            df_standard[col_standard] = df_standard[col_brute]
        else:
            # Chercher des colonnes similaires
            colonnes_similaires = [c for c in df_standard.columns if col_standard in c or col_brute in c]
            if colonnes_similaires:
                df_standard[col_standard] = df_standard[colonnes_similaires[0]]
                logger(f"🔄 Mapping: {colonnes_similaires[0]} -> {col_standard}")
            else:
                df_standard[col_standard] = np.nan
                logger(f"⚠️ Colonne non trouvée: {col_standard}", "warning")
    
    # Garder aussi les colonnes originales pour référence
    for col in df.columns:
        if col not in df_standard.columns:
            df_standard[col] = df[col]
    
    logger(f"Colonnes après mapping: {len(df_standard.columns)}")
    return df_standard

def traiter_dates_simple(df):
    """Traite les colonnes de dates sans filtrage"""
    logger("Traitement des dates...")
    
    df_dates = df.copy()
    
    # Colonnes de dates potentielles
    colonnes_dates = ['date_d_admission', 'date_du_début_de_la_maladie', 'date_de_prélevement', 'date_de_sortie']
    
    for col_date in colonnes_dates:
        if col_date in df_dates.columns:
            df_dates[col_date] = pd.to_datetime(df_dates[col_date], errors='coerce')
            dates_valides = df_dates[col_date].notna().sum()
            logger(f"  {col_date}: {dates_valides} dates valides")
    
    return df_dates

def traiter_ages_simple(df):
    """Traite les colonnes d'âge"""
    logger("Traitement des âges...")
    
    df_ages = df.copy()
    
    # Nettoyer Age_annee
    if 'age_en_année' in df_ages.columns:
        df_ages['age_en_année'] = pd.to_numeric(df_ages['age_en_année'], errors='coerce')
        df_ages.loc[df_ages['age_en_année'] > 120, 'age_en_année'] = np.nan
    
    # Nettoyer Age_mois
    if 'age_en_mois_0_59mois' in df_ages.columns:
        df_ages['age_en_mois_0_59mois'] = pd.to_numeric(df_ages['age_en_mois_0_59mois'], errors='coerce')
        df_ages.loc[df_ages['age_en_mois_0_59mois'] > 59, 'age_en_mois_0_59mois'] = np.nan
    
    return df_ages

def normaliser_valeurs_simple(df):
    """Normalise les valeurs textuelles"""
    logger("Normalisation des valeurs...")
    
    df_normalise = df.copy()
    
    colonnes_a_normaliser = ['sexe_m_f', 'tdr_resultat', 'hospitalisation_oui_non']
    
    for col in colonnes_a_normaliser:
        if col in df_normalise.columns:
            # Convertir en string
            df_normalise[col] = df_normalise[col].fillna('').astype(str)
            df_normalise[col] = df_normalise[col].str.strip().str.capitalize()
            
            # Standardiser
            if col == 'sexe_m_f':
                df_normalise[col] = df_normalise[col].replace({
                    'M': 'Masculin', 'F': 'Feminin', 'H': 'Masculin',
                    'Male': 'Masculin', 'Female': 'Feminin'
                })
    
    return df_normalise

def exporter_donnees(df):
    """Exporte les données"""
    logger("Export des données...")
    
    # CSV pour la base de données
    chemin_csv = DB_DATA_DIR / "cholera_data_compiled.csv"
    df.to_csv(chemin_csv, index=False, encoding='utf-8')
    logger(f"💾 CSV exporté: {chemin_csv}")
    
    # Excel pour analyse
    nom_fichier_excel = f"rdc_compilation_LL_Cholera_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    chemin_excel = DATA_OUTPUTS_DIR / nom_fichier_excel
    
    with pd.ExcelWriter(chemin_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='LL_Cholera', index=False)
    logger(f"💾 Excel exporté: {chemin_excel}")
    
    return chemin_excel, chemin_csv

def generer_rapport(df):
    """Génère un rapport des données"""
    logger("Génération du rapport...")
    
    print("\n" + "="*50)
    print("RAPPORT DE COMPILATION CHOLERA")
    print("="*50)
    print(f"Nombre total de cas: {len(df)}")
    
    if 'sexe_m_f' in df.columns:
        print(f"\nRépartition par sexe:")
        print(df['sexe_m_f'].value_counts(dropna=False).head())
    
    if 'province_de_provenance' in df.columns:
        print(f"\nTop 10 provinces:")
        print(df['province_de_provenance'].value_counts(dropna=False).head(10))
    
    if 'tdr_resultat' in df.columns:
        print(f"\nRésultats TDR:")
        print(df['tdr_resultat'].value_counts(dropna=False).head())
    
    print(f"\nColonnes finales: {len(df.columns)}")
    print("="*50)

def main():
    """Fonction principale simplifiée"""
    logger("Démarrage de la compilation Cholera...")
    
    try:
        # Étape 1: Chargement des données
        df = charger_fichiers_excel()
        
        # Étape 2: Mapping vers le standard
        df = mapper_vers_standard(df)
        
        # Étape 3: Traitements simples
        df = traiter_dates_simple(df)
        df = traiter_ages_simple(df)
        df = normaliser_valeurs_simple(df)
        
        # Étape 4: Export et rapport
        chemin_excel, chemin_csv = exporter_donnees(df)
        generer_rapport(df)
        
        logger("Processus terminé avec succès!", "success")
        logger(f"Fichier Excel: {chemin_excel}")
        logger(f"Fichier CSV: {chemin_csv}")
        
        return df
        
    except Exception as e:
        logger(f"Erreur critique: {e}", "error")
        import traceback
        logger(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    df_final = main()
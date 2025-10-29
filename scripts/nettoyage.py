#!/usr/bin/env python3
"""
Étape 3: Nettoyage approfondi des données
"""

import pandas as pd
import numpy as np
from scripts.config import *
from scripts.utils import *

def traiter_dates(df):
    """Convertit et filtre les dates"""
    logger("Traitement des colonnes de dates...")
    
    df_dates = df.copy()
    
    for col_date in COLONNES_DATES:
        if col_date in df_dates.columns:
            df_dates[col_date] = pd.to_datetime(df_dates[col_date], errors='coerce')
    
    # Filtrer pour l'année cible
    if 'date_admission' in df_dates.columns:
        mask_annee = df_dates['date_admission'].dt.year == CONFIG['annee_filtre']
        df_filtre = df_dates[mask_annee].copy()
        logger(f"Données après filtrage {CONFIG['annee_filtre']}: {len(df_filtre)} lignes")
    else:
        df_filtre = df_dates
        logger("Aucune colonne de date trouvée pour le filtrage", "warning")
    
    return df_filtre

def traiter_ages(df):
    """Traite les colonnes d'âge"""
    logger("Traitement des colonnes d'âge...")
    
    df_ages = df.copy()
    
    # Nettoyer Age_annee
    if 'age_annee' in df_ages.columns:
        df_ages['age_annee'] = pd.to_numeric(df_ages['age_annee'], errors='coerce')
        df_ages.loc[df_ages['age_annee'] > 120, 'age_annee'] = np.nan
    
    # Nettoyer Age_mois
    if 'age_mois' in df_ages.columns:
        df_ages['age_mois'] = pd.to_numeric(df_ages['age_mois'], errors='coerce')
        df_ages.loc[df_ages['age_mois'] > 120, 'age_mois'] = np.nan
    
    # Fusionner Age_annee et Age_mois
    if 'age_annee' in df_ages.columns and 'age_mois' in df_ages.columns:
        df_ages['age'] = df_ages['age_annee']
        df_ages['unite_age'] = 'ans'
        
        # Remplacer par les valeurs en mois si années manquantes
        mask_mois = df_ages['age'].isna() & df_ages['age_mois'].notna()
        df_ages.loc[mask_mois, 'age'] = df_ages.loc[mask_mois, 'age_mois'] / 12
        df_ages.loc[mask_mois, 'unite_age'] = 'mois'
    
    return df_ages

def creer_tranches_age(df):
    """Crée les tranches d'âge"""
    logger("Création des tranches d'âge...")
    
    df_tranches = df.copy()
    
    if 'age' in df_tranches.columns:
        # Tranches d'âge génériques
        conditions = [
            df_tranches['age'] < 1,
            (df_tranches['age'] >= 1) & (df_tranches['age'] < 5),
            (df_tranches['age'] >= 5) & (df_tranches['age'] < 15),
            (df_tranches['age'] >= 15) & (df_tranches['age'] < 50),
            df_tranches['age'] >= 50
        ]
        choices = ['<1 an', '1-4 ans', '5-14 ans', '15-49 ans', '50+ ans']
        
        df_tranches['tranche_age'] = np.select(conditions, choices, default='Inconnu')
        
        # Tranches d'âge en 5 ans
        df_tranches['tranche_age_en_ans'] = pd.cut(
            df_tranches['age'],
            bins=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 120],
            labels=['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', 
                   '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', 
                   '75-79', '80-84', '85-89', '90-94', '95-99', '100+']
        )
    
    return df_tranches

def completer_provinces(df):
    """Complète les informations de province"""
    logger("Complétion des informations géographiques...")
    
    df_provinces = df.copy()
    
    if 'provenance' in df_provinces.columns and 'province_notification' in df_provinces.columns:
        # Remplir province_notification à partir de provenance
        mask_vide = df_provinces['province_notification'].isna()
        
        def trouver_province(provenance):
            if pd.isna(provenance):
                return np.nan
            provenance_str = str(provenance).upper()
            for code, province in CODE_PROVINCES_DEUX_LETTRES.items():
                if code in provenance_str:
                    return province
            return np.nan
        
        df_provinces.loc[mask_vide, 'province_notification'] = df_provinces.loc[mask_vide, 'provenance'].apply(trouver_province)
    
    return df_provinces

def normaliser_valeurs(df):
    """Normalise les valeurs textuelles"""
    logger("Normalisation des valeurs...")
    
    df_normalise = df.copy()
    
    for col in COLONNES_A_NORMALISER:
        if col in df_normalise.columns:
            # Convertir en string et nettoyer
            df_normalise[col] = df_normalise[col].astype(str).str.strip().str.capitalize()
            
            # Standardiser certaines valeurs
            if col == 'sexe':
                df_normalise[col] = df_normalise[col].replace({
                    'M': 'Masculin', 'F': 'Feminin', 'H': 'Masculin',
                    'Male': 'Masculin', 'Female': 'Feminin'
                })
            
            elif col in ['hospitalisation', 'prelevement', 'femme_enceinte']:
                df_normalise[col] = df_normalise[col].replace({
                    'Oui': 'Oui', 'Yes': 'Oui', 'Y': 'Oui', '1': 'Oui',
                    'Non': 'Non', 'No': 'Non', 'N': 'Non', '0': 'Non'
                })
    
    return df_normalise

def ajouter_semaine_epidemiologique(df):
    """Ajoute les informations de semaine épidémiologique"""
    logger("Calcul des semaines épidémiologiques...")
    
    if 'date_admission' in df.columns:
        df_semaine = df.copy()
        df_semaine['num_semaine_epi'] = df_semaine['date_admission'].dt.isocalendar().week
        df_semaine['annee_epi'] = df_semaine['date_admission'].dt.year
        df_semaine['semaine_epid'] = df_semaine['annee_epi'].astype(str) + '-S' + df_semaine['num_semaine_epi'].astype(str).str.zfill(2)
        return df_semaine
    
    return df

def gerer_doublons(df):
    """Gère les doublons dans les données"""
    logger("Gestion des doublons...")
    
    # Compter les doublons
    doublons = df.duplicated(subset=CRITERES_DOUBLONS, keep=False)
    n_doublons = doublons.sum()
    
    logger(f"Doublons détectés: {n_doublons}")
    
    if n_doublons > 0:
        # Supprimer les doublons (garder la première occurrence)
        df_sans_doublons = df.drop_duplicates(subset=CRITERES_DOUBLONS, keep='first')
        logger(f"Après suppression: {len(df_sans_doublons)} lignes")
        return df_sans_doublons
    
    return df

def classer_cas_cholera(df):
    """Classe les cas de choléra (suspects/confirmés)"""
    logger("Classification des cas...")
    
    df_classe = df.copy()
    
    # Critères simplifiés pour la classification
    if 'tdr_resultat' in df_classe.columns and 'symptomes' in df_classe.columns:
        conditions_confirme = df_classe['tdr_resultat'].str.contains('positif', case=False, na=False)
        conditions_suspect = (
            df_classe['symptomes'].str.contains('diarrhée|diarrhee|vomissement', case=False, na=False) |
            df_classe['tdr_resultat'].str.contains('probable|inconnu', case=False, na=False)
        )
        
        df_classe['classification_finale'] = 'Non classé'
        df_classe.loc[conditions_suspect, 'classification_finale'] = 'Suspect'
        df_classe.loc[conditions_confirme, 'classification_finale'] = 'Confirmé'
    
    return df_classe

def executer_nettoyage():
    """Exécute l'étape de nettoyage"""
    logger("=== ÉTAPE 3: NETTOYAGE DES DONNÉES ===")
    
    # Charger les données fusionnées
    df_fusion = charger_etape_precedente(FUSED_DIR, "02_donnees_fusionnees", 'parquet')
    
    # Appliquer les transformations de nettoyage
    df_dates = traiter_dates(df_fusion)
    df_ages = traiter_ages(df_dates)
    df_tranches = creer_tranches_age(df_ages)
    df_provinces = completer_provinces(df_tranches)
    df_normalise = normaliser_valeurs(df_provinces)
    df_semaine = ajouter_semaine_epidemiologique(df_normalise)
    df_doublons = gerer_doublons(df_semaine)
    df_classe = classer_cas_cholera(df_doublons)
    
    # Réorganiser les colonnes dans l'ordre standard
    df_final = filtrer_et_reorganiser_colonnes(df_classe)
    
    # Sauvegarder l'étape
    chemin_sauvegarde = sauvegarder_etape(
        df_final, 
        CLEANED_DIR, 
        "03_donnees_nettoyees", 
        'parquet'
    )
    
    # Générer le rapport
    generer_rapport_etape(df_final, "Nettoyage")
    
    return df_final, chemin_sauvegarde

def main():
    """Fonction principale de nettoyage"""
    try:
        df_nettoye, chemin = executer_nettoyage()
        logger(f"Nettoyage terminé: {chemin}", "success")
        return df_nettoye, chemin
    except Exception as e:
        logger(f"Erreur lors du nettoyage: {e}", "error")
        raise

if __name__ == "__main__":
    main()
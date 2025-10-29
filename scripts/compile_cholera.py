#!/usr/bin/env python3
"""
Script de compilation, fusion et nettoyage des données Cholera
Version adaptée pour l'environnement Docker
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
BASE_DIR = Path(__file__).parent.parent
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
    'motif_fichier': "*_LL_Cholera_*.xlsx",
    'dossier_sortie': DATA_OUTPUTS_DIR,
    'dossier_csv': DB_DATA_DIR,
    'annee_filtre': 2025
}

# Définition des colonnes pour le dataset Cholera
COLONNES_CHOLERA = [
    'provenance', 'n', 'n_epid_prov', 'n_epid', 'statut_a_l_arrivee',
    'date_arrivee_malade', 'date_admission', 'date_notification', 
    'date_investigation', 'date_debut_maladie', 'province_notification',
    'zone_de_sante_notification', 'aire_de_sante_notification', 'semaine_epid',
    'num_semaine_epi', 'annee_epi', 'nom_complet', 'sexe', 'age_annee',
    'age_mois', 'age', 'unite_age', 'age_en_ans', 'tranche_age', 
    'tranche_age_en_ans', 'profession', 'province_provenance',
    'zone_de_sante_provenance', 'aire_de_sante_provenance', 'adresse',
    'symptomes', 'prise_antibiotique_avant_admission', 'nom_antibiotique',
    'antecedents_morbides', 'femme_enceinte', 'degre_deshydratation',
    'plan_de_deshydratation', 'hospitalisation', 'prelevement', 'date_prelevement',
    'tdr_realise', 'tdr_resultat', 'tdr_archive', 'resultat_labo',
    'resultat_labo_culture', 'serotype', 'nom_structure_realisant_le_tdr',
    'resultat_labo_pcr', 'traitement_antibiotique', 'quantite_total_ringer_recue',
    'quantite_total_sro_recue', 'ctc_utc', 'issue', 'date_de_sortie_malade',
    'etat_sortie_malade', 'statut_vaccinal', 'nombre_dose', 'annee_vaccination',
    'source_eventuelle_de_contamination', 'source_approvisionnement_en_eau',
    'classification_finale', 'date_de_guerie', 'observation'
]

# Codes provinces RDC
CODE_PROVINCES_DEUX_LETTRES = {
    'KI': 'Kinshasa', 'KC': 'Kongo Central', 'EQ': 'Equateur',
    'MO': 'Mongala', 'TS': 'Tshuapa', 'TK': 'Tshopo',
    'NK': 'Nord Kivu', 'SK': 'Sud Kivu', 'MN': 'Maniema',
    'KW': 'Kwilu', 'KS': 'Kasai', 'KC': 'Kasai Central', 
    'KE': 'Kasai Oriental', 'LM': 'Lomami', 'SB': 'Sankuru',
    'MB': 'Maindombe', 'TG': 'Tanganyika', 'HL': 'Haut Lomami',
    'HU': 'Haut Uele', 'IT': 'Ituri', 'LU': 'Lualaba'
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

def verifier_fichiers_excel():
    """Vérifie la présence des fichiers Excel"""
    logger("Vérification des fichiers source...")
    
    pattern = CONFIG['dossier_donnees'] / CONFIG['motif_fichier']
    fichiers = glob.glob(str(pattern))
    
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier trouvé avec le pattern: {pattern}")
    
    logger(f"Fichiers trouvés ({len(fichiers)}):")
    for f in fichiers:
        logger(f"  - {os.path.basename(f)}")
    
    return fichiers

def charger_fichiers_excel():
    """Charge et fusionne tous les fichiers Excel"""
    logger("Chargement et fusion des fichiers Excel...")
    
    fichiers = verifier_fichiers_excel()
    dataframes = []
    
    for fichier in fichiers:
        try:
            df = pd.read_excel(fichier, sheet_name="LL_Cholera")
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
    
    return df_fusionne

def nettoyer_noms_colonnes(df):
    """Nettoie les noms de colonnes"""
    logger("Nettoyage des noms de colonnes...")
    
    def clean_column_name(name):
        if pd.isna(name):
            return "colonne_inconnue"
        name = str(name).strip()
        name = re.sub(r'[^\w\s]', '_', name)
        name = re.sub(r'\s+', '_', name)
        return name.lower()
    
    df.columns = [clean_column_name(col) for col in df.columns]
    logger(f"Colonnes après nettoyage: {len(df.columns)}")
    return df

def filtrer_colonnes_cholera(df):
    """Filtre et réorganise les colonnes selon le standard Cholera"""
    logger("Filtrage des colonnes selon le standard Cholera...")
    
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
    
    groupes_colonnes = {
        "zone_de_sante_notification": ['zone_de_sante', 'zone_de_sante_notification'],
        "n_epid": ['n_epid', 'id'],
        "traitement_antibiotique": ['traitement_antibiotique', 'traitement'],
        "province_notification": ['province_notification', 'province']
    }
    
    df_fusion = df.copy()
    
    for nouvelle_col, anciennes_cols in groupes_colonnes.items():
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

def traiter_dates(df):
    """Convertit et filtre les dates"""
    logger("Traitement des colonnes de dates...")
    
    colonnes_dates = [
        'date_arrivee_malade', 'date_admission', 'date_debut_maladie',
        'date_prelevement', 'date_de_sortie_malade'
    ]
    
    df_dates = df.copy()
    
    for col_date in colonnes_dates:
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
    
    colonnes_a_normaliser = [
        'sexe', 'tdr_resultat', 'resultat_labo_pcr', 'issue',
        'hospitalisation', 'prelevement', 'femme_enceinte'
    ]
    
    df_normalise = df.copy()
    
    for col in colonnes_a_normaliser:
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
    
    colonnes_identifiantes = [
        'nom_complet', 'province_notification', 'zone_de_sante_notification',
        'sexe', 'age', 'profession'
    ]
    
    # Compter les doublons
    doublons = df.duplicated(subset=colonnes_identifiantes, keep=False)
    n_doublons = doublons.sum()
    
    logger(f"Doublons détectés: {n_doublons}")
    
    if n_doublons > 0:
        # Supprimer les doublons (garder la première occurrence)
        df_sans_doublons = df.drop_duplicates(subset=colonnes_identifiantes, keep='first')
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

def exporter_donnees(df):
    """Exporte les données vers Excel et CSV"""
    logger("Export des données...")
    
    # Exporter vers Excel
    nom_fichier_excel = f"rdc_compilation_LL_Cholera_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    chemin_excel = CONFIG['dossier_sortie'] / nom_fichier_excel
    
    try:
        with pd.ExcelWriter(chemin_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='LL_Cholera', index=False)
        logger(f"Excel exporté: {chemin_excel}")
    except Exception as e:
        logger(f"Erreur export Excel: {e}", "error")
    
    # Exporter vers CSV (pour la base de données)
    nom_fichier_csv = "cholera_data_compiled.csv"
    chemin_csv = CONFIG['dossier_csv'] / nom_fichier_csv
    
    try:
        df.to_csv(chemin_csv, index=False, encoding='utf-8')
        logger(f"CSV exporté: {chemin_csv}")
    except Exception as e:
        logger(f"Erreur export CSV: {e}", "error")
    
    return chemin_excel, chemin_csv

def generer_rapport(df):
    """Génère un rapport sommaire des données"""
    logger("Génération du rapport...")
    
    print("\n" + "="*50)
    print("RAPPORT DE COMPILATION CHOLERA")
    print("="*50)
    print(f"Nombre total de cas: {len(df)}")
    
    if 'sexe' in df.columns:
        print(f"\nRépartition par sexe:")
        print(df['sexe'].value_counts(dropna=False))
    
    if 'province_notification' in df.columns:
        print(f"\nTop 10 provinces:")
        print(df['province_notification'].value_counts(dropna=False).head(10))
    
    if 'classification_finale' in df.columns:
        print(f"\nClassification des cas:")
        print(df['classification_finale'].value_counts(dropna=False))
    
    if 'num_semaine_epi' in df.columns:
        print(f"\nPériode couverte: Semaines {df['num_semaine_epi'].min()} à {df['num_semaine_epi'].max()}")
    
    print(f"\nColonnes finales: {len(df.columns)}")
    print("="*50)

def main():
    """Fonction principale"""
    logger("Démarrage de la compilation Cholera...")
    
    try:
        # Étape 1: Chargement des données
        df = charger_fichiers_excel()
        
        # Étape 2: Nettoyage des colonnes
        df = nettoyer_noms_colonnes(df)
        df = filtrer_colonnes_cholera(df)
        
        # Étape 3: Fusion des colonnes similaires
        df = fusionner_colonnes_similaires(df)
        
        # Étape 4: Traitement des dates
        df = traiter_dates(df)
        
        # Étape 5: Nettoyage des données
        df = traiter_ages(df)
        df = creer_tranches_age(df)
        df = completer_provinces(df)
        df = normaliser_valeurs(df)
        df = ajouter_semaine_epidemiologique(df)
        
        # Étape 6: Gestion de la qualité
        df = gerer_doublons(df)
        df = classer_cas_cholera(df)
        
        # Étape 7: Réorganisation finale
        df = filtrer_colonnes_cholera(df)  # Remettre dans l'ordre standard
        
        # Étape 8: Export et rapport
        chemin_excel, chemin_csv = exporter_donnees(df)
        generer_rapport(df)
        
        logger("Processus terminé avec succès!", "success")
        logger(f"Fichier Excel: {chemin_excel}")
        logger(f"Fichier CSV: {chemin_csv}")
        
        return df
        
    except Exception as e:
        logger(f"Erreur critique: {e}", "error")
        sys.exit(1)

if __name__ == "__main__":
    df_final = main()
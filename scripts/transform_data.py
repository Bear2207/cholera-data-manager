#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from utils import setup_logging, validate_dataframe

logger = setup_logging()

def handle_duplicates(df):
    """
    Gérer les doublons dans les données
    """
    logger.info("Gestion des doublons")
    
    # Filtrer pour 2025
    df_2025 = df[df['Annee_epi'] == 2025].copy()
    
    # Critères de doublons
    critere_doublons = [
        "Nom_complet", "Province_notification", "Zone_de_sante_notification",
        "Aire_de_sante_notification", "Sexe", "Age", "Unite_age", "Profession"
    ]
    
    # Compter les doublons
    nbr_doublons = gerer_doublons_avance(
        df_2025, 
        critere_doublons,
        mode='compter_lignes', 
        tri_ascendant=True, 
        reset_index=True
    )
    
    logger.info(f"Nombre de doublons détectés: {nbr_doublons}")
    
    # Supprimer les doublons
    df_sans_doublons = gerer_doublons_avance(
        df_2025,
        colonnes_inclues=critere_doublons,
        mode='nettoyer',
        tri_ascendant=True,
        reset_index=True,
        keep='first' 
    )
    
    # Réorganiser les colonnes
    from clean_data import COLONNES_CHOLERA
    df_sans_doublons = reclasser_colonnes(
        df_sans_doublons, 
        colonnes_prioritaires=COLONNES_CHOLERA
    )
    
    return df_sans_doublons

def classify_cases(df):
    """
    Classer les cas en suspects et confirmés
    """
    logger.info("Classification des cas")
    
    df_classified = df.copy()
    
    # Critères de suspicion
    critere_suspect = {
        "TDR_Resultat": ["Positif", "probable", "inconnu"],
        "Symptomes": [
            "DIARRHEE", "DESHYDRATATION", 
            "DIARRHEES ET VOMISSENTS", 
            "SEULLES LIQUIDE ET VOMISSENT"
        ]
    }
    
    # Critères de confirmation
    critere_confirme = {
        "TDR_realise": "Positif"
    }
    
    df_classified = classer_cas(
        df=df_classified,
        critere_suspect=critere_suspect,    
        critere_confirme=critere_confirme,
        regex_mode=True,
        nom_maladie="Cholera"
    )
    
    return df_classified

def add_epidemiological_columns(df):
    """
    Ajouter les colonnes épidémiologiques
    """
    logger.info("Ajout des colonnes épidémiologiques")
    
    df_transformed = df.copy()
    
    colonnes_datetime = [
        'Date_arrivee_malade', 'Date_admission', 'Date_debut_maladie',
        'Date_prelevement', 'Date_de_sortie_malade'
    ]
    
    # Ajouter année et semaine épidémiologique
    df_transformed = ajouter_annee_semaine_epi(
        df_transformed,
        colonnes_datetime,
        'Semaine_epid',
        separer_colonnes=True,
        remplacer_si_existe=True,
        ordre="semaine-annee"
    )
    
    # Correction de l'année épidémiologique
    df_transformed["Annee_epi"] = df_transformed["Annee_epi"].replace({2035: 2025})
    
    return df_transformed

def finalize_data_cleaning(df):
    """
    Finaliser le nettoyage des données
    """
    logger.info("Finalisation du nettoyage des données")
    
    df_final = df.copy()
    
    # Forcer la conversion des colonnes d'âge en numérique
    df_final['Age_annee'] = pd.to_numeric(df_final['Age_annee'], errors='coerce')
    df_final['Age_mois'] = pd.to_numeric(df_final['Age_mois'], errors='coerce')
    
    # Supprimer les valeurs aberrantes
    df_final.loc[df_final['Age_annee'] > 120, 'Age_annee'] = float('nan')
    df_final.loc[df_final['Age_mois'] > 120, 'Age_mois'] = float('nan')
    
    # Recréer les tranches d'âge
    df_final = creer_tranche_age_avec_unite_generique(
        df_final, 'Age', 'Unite_age'
    )
    
    # Normalisation finale
    colonnes_geographiques = [
        'Province_notification', 'Zone_de_sante_notification', 
        'Aire_de_sante_notification', 'Province_provenance',
        'Zone_de_sante_provenance', 'Aire_de_sante_provenance'
    ]
    
    df_final = normaliser_values(
        df_final,
        colonnes_geographiques,
        case_option='title',
        remove_accents=True
    )
    
    # Nettoyer les valeurs vides
    df_final = nettoyer_valeurs_vides(df_final)
    
    return df_final

def prepare_analysis_data(df, semaine_epi_min=1, semaine_epi_max=41):
    """
    Préparer les données pour l'analyse
    """
    logger.info("Préparation des données pour l'analyse")
    
    # Filtrer par semaine épidémiologique
    df_analysis = df.loc[
        df['Num_semaine_epi'].between(semaine_epi_min, semaine_epi_max)
    ].copy()
    
    # Nettoyer les colonnes pour l'étude
    colonnes_a_verifier = [
        'Sexe', 'Resultat_labo', 'Issue', 'Statut_vaccinal', 'Symptomes', 
        'Femme_enceinte', 'Degre_deshydratation', 'Hospitalisation',
        'Prelevement', 'TDR_realise', 'TDR_Resultat'
    ]
    
    df_analysis = clean_all_values(
        df_analysis, 
        cols=colonnes_a_verifier,
        case_option='capitalize', 
        remove_accents=True
    )
    
    return df_analysis
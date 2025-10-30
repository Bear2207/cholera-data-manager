#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from utils import setup_logging, validate_dataframe

logger = setup_logging()

# Configuration des colonnes
COLONNES_CHOLERA = [
    'Provenance', 'N', 'N_epid_prov', 'N_epid', 'Statut_a_l_arrivee',
    'Date_arrivee_malade', 'Date_admission', 'Date_notification', 
    'Date_investigation', 'Date_debut_maladie', 'Province_notification',
    'Zone_de_sante_notification', 'Aire_de_sante_notification', 'Semaine_epid',
    'Num_semaine_epi', 'Annee_epi', 'Nom_complet', 'Sexe', 'Age_annee',
    'Age_mois', 'Age', 'Unite_age', 'Age_en_ans', 'Tranche_age', 
    'Tranche_age_en_ans', 'Profession', 'Province_provenance',
    'Zone_de_sante_provenance', 'Aire_de_sante_provenance', 'Adresse',
    'Symptomes', 'Prise_antibiotique_avant_admission', 'Nom_antibiotique',
    'Antecedents_morbides', 'Femme_enceinte', 'Degre_deshydratation',
    'Plan_de_deshydratation', 'Hospitalisation', 'Prelevement',
    'Date_prelevement', 'TDR_realise', 'TDR_Resultat', 'TDR_archive',
    'Resultat_labo', 'Resultat_labo_culture', 'Serotype',
    'Nom_structure_realisant_le_tdr', 'Resultat_labo_pcr',
    'Traitement_antibiotique', 'Quantite_total_ringer_recue',
    'Quantite_total_sro_recue', 'Ctc_utc', 'Issue', 'Date_de_sortie_malade',
    'Etat_sortie_malade', 'Statut_vaccinal', 'Nombre_dose', 'Annee_vaccination',
    'Source_eventuelle_de_contamination', 'Source_approvisionnement_en_eau',
    'Classification_finale', 'Date_de_guerie', 'Observation'
]

def preprocess_columns(df):
    """
    Prétraiter les colonnes: sélection, ajout et réorganisation
    """
    logger.info("Prétraitement des colonnes")
    
    df_processed = df.copy()
    
    # Supprimer les colonnes inutiles
    df_processed = supprimer_colonnes_inutiles(
        df_processed, 
        colonnes_a_garder=COLONNES_CHOLERA
    )
    
    # Ajouter les colonnes manquantes
    df_processed = ajouter_colonnes_manquantes(
        df_processed, 
        colonnes=COLONNES_CHOLERA
    )
    
    # Réorganiser les colonnes
    df_processed = reclasser_colonnes(
        df_processed, 
        colonnes_prioritaires=COLONNES_CHOLERA
    )
    
    return df_processed

def merge_similar_columns(df):
    """
    Fusionner les colonnes similaires
    """
    logger.info("Fusion des colonnes similaires")
    
    df_merged = clean_all_column_names(df.copy())
    
    # Fusion automatique par similarité
    df_merged = fusionner_colonnes_similaires_ou_groupes(
        df_merged,
        method="similarity",
        type_fusion="first_non_null",
        seuil_similarite=1,
        drop=True
    )
    
    # Fusion manuelle de colonnes spécifiques
    colonnes_a_fusionner = {
        "Zone_de_sante_notification": ['Zone_de_sante','Zone_de_sante_notification'],
        "N_epid": ['N_epid', 'Id'],
        "Traitement_antibiotique": ['Traitement_antibiotique','Traitement'],
        "Province_notification": ['Province_notification','Province'],
        "Zone_de_sante_notification": ['Zone_de_sante_notification', 'Zone_de_sante']
    }
    
    df_merged = fusionner_colonnes_similaires_ou_groupes(
        df_merged,
        method="manual",
        groupes_colonnes=colonnes_a_fusionner,
        type_fusion="first_non_null",
        drop=True
    )
    
    return df_merged

def clean_dates(df):
    """
    Nettoyer et convertir les colonnes de dates
    """
    logger.info("Nettoyage des dates")
    
    df_cleaned = df.copy()
    colonnes_datetime = [
        'Date_arrivee_malade', 'Date_admission', 'Date_debut_maladie',
        'Date_prelevement', 'Date_de_sortie_malade'
    ]
    
    # Conversion en datetime
    df_cleaned = convert_column_to_date(df_cleaned, colonnes_datetime)
    
    # Filtrage par année 2025
    df_cleaned = filtrer_par_premiere_date(df_cleaned, colonnes_datetime, 2025)
    
    return df_cleaned

def clean_demographic_data(df):
    """
    Nettoyer les données démographiques
    """
    logger.info("Nettoyage des données démographiques")
    
    df_cleaned = df.copy()
    
    # Nettoyage des noms
    df_cleaned = clean_all_values(
        df_cleaned, 
        cols='Nom_complet', 
        case_option="upper", 
        remove_accents=True,
        convert_type=False,
        verbose=False
    )
    
    # Uniformiser les âges en années
    df_cleaned['Age_annee'] = df_cleaned['Age_annee'].apply(
        lambda x: extraire_texte_et_nombre(
            x,
            valeur_par_defaut="ans",
            detecter_annee=True,
            normaliser_texte=True,
            mode="nombre"
        )
    ).astype(float)
    
    # Uniformiser les âges en mois
    df_cleaned['Age_mois'] = df_cleaned['Age_mois'].apply(
        lambda x: extraire_texte_et_nombre(
            x,
            valeur_par_defaut="mois",
            detecter_annee=True,
            normaliser_texte=True,
            mode="nombre"
        )
    ).astype(float)
    
    # Fusionner les colonnes d'âge
    df_cleaned = fusionner_colonnes_Age_annee_Age_mois(
        df_cleaned, 
        col_age_annee="Age_annee", 
        col_age_mois="Age_mois", 
        nom_colonne_age="Age", 
        nom_colonne_unite="Unite_age", 
        age_limite_en_annees=5.0, 
        arrondi_mois=1, 
        arrondi_annees=2, 
        drop_originals=False
    )
    
    # Créer les tranches d'âge
    df_cleaned = creer_tranche_age_avec_unite_generique(
        df_cleaned, 'Age', 'Unite_age'
    )
    
    df_cleaned = creer_tranche_age_avec_unite(
        df_cleaned,
        col_age='Age',
        col_unite='Unite_age',
        mode='5ans',
        col_tranche='Tranche_age_en_ans'
    )
    
    return df_cleaned

def clean_geographic_data(df):
    """
    Nettoyer les données géographiques
    """
    logger.info("Nettoyage des données géographiques")
    
    df_cleaned = df.copy()
    
    # Compléter les provinces
    code_provinces_deux_lettres = {}  # À définir selon vos besoins
    df_cleaned["Province_notification"] = df_cleaned["Provenance"].apply(
        lambda x: trouver_province(x, code_provinces_deux_lettres)
    )
    
    # Remplir les zones de santé
    dictionnaires = creer_dictionnaires_pyramide(df_ref=clean_database_pyramide())
    df_cleaned = remplir_colonne_depuis_reference(
        df=df_cleaned,
        colonne_a_remplir="Zone_de_sante_notification",
        colonne_reference=["N_epid_prov","N_epid"],
        type_reference="N_epid",
        dictionnaires=dictionnaires,
        variable_remplissage="Zone_de_sante"
    )
    
    # Nettoyer les zones et aires de santé
    df_ref = pd.read_excel("data/rdc_database_pyramide_code.xlsx")
    colonnes_a_nettoyer = ["Zone_de_sante_notification", "Aire_de_sante_notification"]
    
    mapping_colonnes = {
        "Province_notification": "Province",
        "Province_provenance": "Province",
        "Zone_de_sante_notification": "Zone_de_sante",
        "Zone_de_sante_provenance": "Zone_de_sante",
        "Aire_de_sante_notification": "Aire_de_sante",
        "Aire_de_sante_provenance": "Aire_de_sante"
    }
    
    df_cleaned = nettoyer_colonnes(
        df_cleaned, 
        df_ref,
        col_dirty_boucle="Province_notification",
        cols_a_nettoyer=colonnes_a_nettoyer,
        mapping_colonnes=mapping_colonnes,
        seuil=85
    )
    
    # Normalisation des noms géographiques
    colonnes_geographiques = [
        'Province_notification', 'Zone_de_sante_notification', 
        'Aire_de_sante_notification', 'Province_provenance',
        'Zone_de_sante_provenance', 'Aire_de_sante_provenance'
    ]
    
    df_cleaned = normaliser_values(
        df_cleaned, 
        colonnes_geographiques, 
        case_option='title',
        remove_accents=True
    )
    
    return df_cleaned

def clean_categorical_data(df):
    """
    Nettoyer les données catégorielles
    """
    logger.info("Nettoyage des données catégorielles")
    
    df_cleaned = df.copy()
    
    # Colonnes avec première lettre en majuscule
    colonnes_capitalize = [
        'Profession', 'Prise_antibiotique_avant_admission', 
        'Antecedents_morbides', 'Femme_enceinte', 'Hospitalisation',
        'Prelevement', 'TDR_realise', 'Traitement_antibiotique',
        'Degre_deshydratation', 'Source_approvisionnement_en_eau',
        'TDR_Resultat', 'TDR_Archive', 'Issue', 'Observation',
        'Resultat_labo_pcr', 'Statut_vaccinal'
    ]
    
    colonnes_oui_non = [
        'Prise_antibiotique_avant_admission', 'Antecedents_morbides',
        'Femme_enceinte', 'Hospitalisation', 'Prelevement', 
        'TDR_realise', 'Traitement_antibiotique'
    ]
    
    df_cleaned = clean_all_values(
        df_cleaned,
        colonnes_capitalize + colonnes_oui_non,
        case_option='capitalize',
        remove_accents=True
    )
    
    return df_cleaned

def replace_specific_values(df):
    """
    Remplacer les valeurs spécifiques selon les critères
    """
    logger.info("Remplacement des valeurs spécifiques")
    
    df_cleaned = df.copy()
    
    critere = {
        "Sexe": "Sexe",
        "TDR_realise": "TDR_realise",
        "TDR_Resultat": "TDR_Resultat",
        "Resultat_labo": "Resultat_labo",
        "Resultat_labo_pcr": "Resultat_labo_pcr",
        "Prelevement": "Prelevement",
        "Hospitalisation": "Hospitalisation",
        "Degre_deshydratation": "Degre_deshydratation",
        "Prise_antibiotique_avant_admission": "Prise_antibiotique_avant_admission",
        "Resultat_labo_culture": "Resultat_labo_culture",
        "Issue": "Issue"
    }
    
    df_cleaned = replace_specific_values_critere(
        df=df_cleaned,
        critere=critere,
        mapping_file="data/Replace_values.xlsx",
        regex_mode=True,
        clean_before=True,
        strip_lower=True
    )
    
    return df_cleaned
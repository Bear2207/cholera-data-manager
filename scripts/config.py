#!/usr/bin/env python3
"""
Configuration centrale pour le pipeline Cholera
"""

import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "cholera"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
DB_DATA_DIR = BASE_DIR / "db" / "data"

# Sous-dossiers pour chaque étape
COMPILED_DIR = DATA_PROCESSED_DIR / "compiled"
FUSED_DIR = DATA_PROCESSED_DIR / "fused" 
CLEANED_DIR = DATA_PROCESSED_DIR / "cleaned"

# Création des dossiers
for directory in [DATA_RAW_DIR, COMPILED_DIR, FUSED_DIR, CLEANED_DIR, DATA_OUTPUTS_DIR, DB_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Paramètres de traitement
CONFIG = {
    'dossier_donnees': DATA_RAW_DIR,
    'motif_fichier': "*_LL_Cholera_*.xlsx",
    'nom_feuille': "LL_Cholera",
    'annee_filtre': 2025,
    'semaine_epi_min': 1,
    'semaine_epi_max': 41
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

# Groupes de colonnes pour la fusion
GROUPES_COLONNES_FUSION = {
    "zone_de_sante_notification": ['zone_de_sante', 'zone_de_sante_notification'],
    "n_epid": ['n_epid', 'id'],
    "traitement_antibiotique": ['traitement_antibiotique', 'traitement'],
    "province_notification": ['province_notification', 'province']
}

# Colonnes de dates
COLONNES_DATES = [
    'date_arrivee_malade', 'date_admission', 'date_debut_maladie',
    'date_prelevement', 'date_de_sortie_malade'
]

# Colonnes à normaliser
COLONNES_A_NORMALISER = [
    'sexe', 'tdr_resultat', 'resultat_labo_pcr', 'issue',
    'hospitalisation', 'prelevement', 'femme_enceinte'
]

# Critères pour les doublons
CRITERES_DOUBLONS = [
    'nom_complet', 'province_notification', 'zone_de_sante_notification',
    'sexe', 'age', 'profession'
]
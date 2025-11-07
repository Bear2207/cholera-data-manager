"""Configuration globale du pipeline (chemins, motifs, colonnes prioritaires).
"""
from pathlib import Path

# Dossier racine du projet (modifiable)
BASE_DIR = Path(__file__).parent

# Dossiers de données
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = r"C:\Users\Benjamin MUPANZI\Documents\dataminsante\Cholera\SE41"  # valeur par défaut initiale
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Paramètres du fichier
MOTIF_FICHIER = "*_LL_Cholera_*.xlsx"
NOM_FEUILLE = "LL_Cholera"

# Colonnes prioritaires attendues (liste extraite de ton script original)
COLONNES_CHOLERA = [
    'Provenance', 'N', 'N_epid_prov', 'N_epid', 'Statut_a_l_arrivee',
    'Date_arrivee_malade','Date_admission','Date_notification','Date_investigation','Date_debut_maladie',
    'Province_notification','Zone_de_sante_notification','Aire_de_sante_notification','Semaine_epid',
    'Num_semaine_epi','Annee_epi','Nom_complet','Sexe','Age_annee','Age_mois','Age','Unite_age',
    'Age_en_ans','Tranche_age','Tranche_age_en_ans','Profession','Province_provenance',
    'Zone_de_sante_provenance','Aire_de_sante_provenance','Adresse','Symptomes','Prise_antibiotique_avant_admission',
    'Nom_antibiotique','Antecedents_morbides','Femme_enceinte','Degre_deshydratation','Plan_de_deshydratation',
    'Hospitalisation','Prelevement','Date_prelevement','TDR_realise','TDR_Resultat','TDR_archive','Resultat_labo',
    'Resultat_labo_culture','Serotype','Nom_structure_realisant_le_tdr','Resultat_labo_pcr','Traitement_antibiotique',
    'Quantite_total_ringer_recue','Quantite_total_sro_recue','Ctc_utc','Issue','Date_de_sortie_malade','Etat_sortie_malade',
    'Statut_vaccinal','Nombre_dose','Annee_vaccination','Source_eventuelle_de_contamination','Source_approvisionnement_en_eau',
    'Classification_finale','Date_de_guerie','Observation'
]

# Colonnes datetime utilisées fréquemment
DATETIME_COLS = ['Date_arrivee_malade','Date_admission','Date_debut_maladie','Date_prelevement','Date_de_sortie_malade']

# Valeurs par défaut pour export
DEFAULT_SHEET_NAME = "LL_Cholera"
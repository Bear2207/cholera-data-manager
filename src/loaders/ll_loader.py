import pandas as pd
from pathlib import Path
from numbers import Number

LL_COLUMNS = [
    'n_epid_prov', 'n_epid', 'statut_a_l_arrivee', 'date_arrivee_malade',
    'date_admission_au_ct', 'date_notification', 'date_investigation',
    'date_debut_maladie', 'province_notification', 'zone_de_sante_notification',
    'aire_de_sante_notification', 'semaine_epid', 'num_semaine_epid', 'annee_epid',
    'nom_complet', 'sexe', 'age_annee', 'age_mois', 'age', 'unite_age',
    'age_en_ans', 'tranche_age', 'tranche_age_en_ans', 'profession', 'province_provenance',
    'zone_de_sante_provenance', 'aire_de_sante_provenance', 'adresse', 'symptomes',
    'prise_antibiotique_avant_admission', 'nom_antibiotique', 'antecedents_morbides',
    'femme_enceinte', 'degre_deshydratation', 'plan_de_deshydratation',
    'hospitalisation', 'prelevement', 'date_prelevement', 'tdr_realise',
    'tdr_resultat', 'tdr_archive', 'resultat_labo', 'resultat_labo_culture',
    'serotype', 'nom_structure_realisant_le_tdr', 'resultat_labo_pcr',
    'traitement_antibiotique', 'quantite_total_ringer_recue',
    'quantite_total_sro_recue', 'ctc_utc', 'issue', 'date_sortie_au_ct',
    'etat_sortie_malade', 'statut_vaccinal', 'nombre_dose', 'annee_vaccination',
    'source_eventuelle_de_contamination', 'source_approvisionnement_en_eau',
    'classification_finale', 'date_de_guerie', 'observation', 'est_cas_suspect',
    'est_cas_confirme', 'classification_auto'
]

BOOLEAN_COLUMNS = [
    'est_cas_suspect', 'est_cas_confirme'
]

DATE_COLUMNS = [
    'date_arrivee_malade', 'date_admission_au_ct', 'date_notification',
    'date_investigation', 'date_debut_maladie', 'date_prelevement',
    'date_sortie_au_ct', 'date_de_guerie'
]

TRUE_VALUES = {'1', 'true', 't', 'yes', 'y', 'oui', 'o', 'vrai'}
FALSE_VALUES = {'0', 'false', 'f', 'no', 'n', 'non', 'faux'}

def _parse_boolean(value):
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Number):
        if value == 1:
            return True
        if value == 0:
            return False
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None

def _normalize_boolean_column(series: pd.Series) -> pd.Series:
    normalized = series.map(_parse_boolean)
    unknown = sorted(
        str(value).strip()
        for value in series[normalized.isna() & series.notna()].unique()
        if str(value).strip()
    )
    if unknown:
        sample = ', '.join(unknown[:10])
        raise ValueError(f"Valeurs booleennes non reconnues dans {series.name}: {sample}")
    return normalized

def load_ll_excel(filepath: Path) -> pd.DataFrame:
    """Charge un fichier LL et l'aligne sur les colonnes insérables."""
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier LL introuvable : {filepath}")
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    if 'LL_Cholera' not in xl.sheet_names:
        raise ValueError(f"Feuille 'LL_Cholera' absente dans {filepath}")
    df = pd.read_excel(filepath, sheet_name='LL_Cholera', engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        'N_epid_prov': 'n_epid_prov', 'N_epid': 'n_epid', 'Statut_a_l_arrivee': 'statut_a_l_arrivee',
        'Date_arrivee_malade': 'date_arrivee_malade', 'Date_admission_au_CT': 'date_admission_au_ct',
        'Date_notification': 'date_notification', 'Date_investigation': 'date_investigation',
        'Date_debut_maladie': 'date_debut_maladie', 'Province_notification': 'province_notification',
        'Zone_de_sante_notification': 'zone_de_sante_notification',
        'Aire_de_sante_notification': 'aire_de_sante_notification', 'Semaine_epid': 'semaine_epid',
        'Num_semaine_epid': 'num_semaine_epid', 'Annee_epid': 'annee_epid', 'Nom_complet': 'nom_complet',
        'Sexe': 'sexe', 'Age_annee': 'age_annee', 'Age_mois': 'age_mois', 'Age': 'age',
        'Unite_age': 'unite_age', 'Age_en_ans': 'age_en_ans', 'Tranche_age': 'tranche_age',
        'Tranche_age_en_ans': 'tranche_age_en_ans', 'Profession': 'profession',
        'Province_provenance': 'province_provenance', 'Zone_de_sante_provenance': 'zone_de_sante_provenance',
        'Aire_de_sante_provenance': 'aire_de_sante_provenance', 'Adresse': 'adresse',
        'Symptomes': 'symptomes', 'Prise_antibiotique_avant_admission': 'prise_antibiotique_avant_admission',
        'Nom_antibiotique': 'nom_antibiotique', 'Antecedents_morbides': 'antecedents_morbides',
        'Femme_enceinte': 'femme_enceinte', 'Degre_deshydratation': 'degre_deshydratation',
        'Plan_de_deshydratation': 'plan_de_deshydratation', 'Hospitalisation': 'hospitalisation',
        'Prelevement': 'prelevement', 'Date_prelevement': 'date_prelevement', 'TDR_realise': 'tdr_realise',
        'TDR_Resultat': 'tdr_resultat', 'TDR_archive': 'tdr_archive', 'Resultat_labo': 'resultat_labo',
        'Resultat_labo_culture': 'resultat_labo_culture', 'Serotype': 'serotype',
        'Nom_structure_realisant_le_tdr': 'nom_structure_realisant_le_tdr', 'Resultat_labo_pcr': 'resultat_labo_pcr',
        'Traitement_antibiotique': 'traitement_antibiotique', 'Quantite_total_ringer_recue': 'quantite_total_ringer_recue',
        'Quantite_total_sro_recue': 'quantite_total_sro_recue', 'Ctc_utc': 'ctc_utc', 'Issue': 'issue',
        'Date_sortie_au_CT': 'date_sortie_au_ct', 'Etat_sortie_malade': 'etat_sortie_malade',
        'Statut_vaccinal': 'statut_vaccinal', 'Nombre_dose': 'nombre_dose',
        'Annee_vaccination': 'annee_vaccination',
        'Source_eventuelle_de_contamination': 'source_eventuelle_de_contamination',
        'Source_approvisionnement_en_eau': 'source_approvisionnement_en_eau',
        'Classification_finale': 'classification_finale', 'Date_de_guerie': 'date_de_guerie',
        'Observation': 'observation', 'est_cas_suspect': 'est_cas_suspect',
        'est_cas_confirme': 'est_cas_confirme', 'classification_auto': 'classification_auto'
    }
    df = df.rename(columns=rename_map)
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True).dt.date
    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = _normalize_boolean_column(df[col])
    return df[[col for col in LL_COLUMNS if col in df.columns]]
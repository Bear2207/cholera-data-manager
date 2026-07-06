#!/usr/bin/env python3
"""Loader moderne pour charger les fichiers Excel dans la base Postgres.

Usage:
  pip install -r requirements.txt
  python scripts/load_data.py

Configuration via variables d'environnement (optionnel):
  POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT

Le script charge :
  - db/IDS_2026.xlsx (feuille 'IDS_RDC') -> schema cholera.cas_maladie
  - db/rdc_compilation*_LL_Cholera_*.xlsx (feuille 'LL_Cholera') -> cholera.cas_ll
"""
from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / 'db'


def get_engine():
    user = os.environ.get('POSTGRES_USER', 'bearing')
    password = os.environ.get('POSTGRES_PASSWORD', 'Couspdata')
    db = os.environ.get('POSTGRES_DB', 'ids_db')
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
    return create_engine(url)


def load_ids(engine):
    path = DB_DIR / 'IDS_2026.xlsx'
    if not path.exists():
        print('IDS file not found:', path)
        return
    print('Loading', path)
    df = pd.read_excel(path, sheet_name='IDS_RDC', engine='openpyxl')

    # Rename columns to match DB
    df = df.rename(columns={
        'NUM': 'code_zone', 'PAYS': 'pays', 'PROV': 'province', 'ZS': 'zone_sante',
        'POP': 'population', 'NUMSEM': 'num_semaine', 'DEBUTSEM': 'debut_semaine_originale',
        'MALADIE': 'maladie', 'C328TNN': 'cas_tnn', 'DTNN': 'deces_tnn',
        'C011MOIS': 'cas_0_11_mois', 'D011MOIS': 'deces_0_11_mois',
        'C1259MOIS': 'cas_12_59_mois', 'D1259MOIS': 'deces_12_59_mois',
        'C515ANS': 'cas_5_15_ans', 'D515ANS': 'deces_5_15_ans',
        'CP15ANS': 'cas_15_plus', 'DP15ANS': 'deces_15_plus',
        'TOTALCAS': 'cas_total', 'TOTALDECES': 'deces_total',
        'LETAL': 'letalite', 'ATTAQ': 'taux_attaque',
        'RecStatus': 'rec_status', 'UniqueKey': 'unique_key', 'ANNEE': 'annee'
    })

    # Compute debut_semaine if missing
    if 'debut_semaine_originale' in df.columns and 'debut_semaine' not in df.columns:
        df['debut_semaine'] = pd.to_datetime(df['debut_semaine_originale'], errors='coerce')

    # Ensure numeric columns
    int_cols = ['population','num_semaine','cas_tnn','deces_tnn','cas_0_11_mois','deces_0_11_mois',
                'cas_12_59_mois','deces_12_59_mois','cas_5_15_ans','deces_5_15_ans','cas_15_plus',
                'deces_15_plus','cas_total','deces_total','rec_status','unique_key']
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('Int64')

    # Select and order columns present in DB
    cols = [
        'code_zone','pays','province','zone_sante','population','num_semaine','annee','debut_semaine_originale','debut_semaine',
        'maladie','cas_tnn','deces_tnn','cas_0_11_mois','deces_0_11_mois','cas_12_59_mois','deces_12_59_mois',
        'cas_5_15_ans','deces_5_15_ans','cas_15_plus','deces_15_plus','cas_total','deces_total','letalite','taux_attaque','rec_status','unique_key'
    ]
    df = df[[c for c in cols if c in df.columns]]

    with engine.begin() as conn:
        # Ensure schema exists
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS cholera'))
        df.to_sql('cas_maladie', conn, schema='cholera', if_exists='append', index=False, method='multi')
    print('Loaded IDS rows:', len(df))


def load_ll(engine):
    # Find any rdc_compilation LL files
    files = list(DB_DIR.glob('rdc_compilation*_LL_Cholera_*.xlsx'))
    if not files:
        # fallback to known filename
        possible = DB_DIR / 'rdc_compilation_LL_Cholera_SE01_SE52_04_01_2026_03_33_36.xlsx'
        files = [possible] if possible.exists() else []
    loaded = 0
    for path in files:
        if not path.exists():
            continue
        print('Loading LL file', path)
        xl = pd.ExcelFile(path, engine='openpyxl')
        if 'LL_Cholera' not in xl.sheet_names:
            print('No LL_Cholera sheet in', path)
            continue
        df = pd.read_excel(path, sheet_name='LL_Cholera', engine='openpyxl')

        # Standardize column names (replace spaces and case)
        df.columns = [c.strip() for c in df.columns]
        # Keep only columns that exist in DB or are useful
        rename_map = {
            'N_epid_prov':'n_epid_prov','N_epid':'n_epid','Statut_a_l_arrivee':'statut_a_l_arrivee',
            'Date_arrivee_malade':'date_arrivee_malade','Date_admission_au_CT':'date_admission_au_ct',
            'Date_notification':'date_notification','Date_investigation':'date_investigation','Date_debut_maladie':'date_debut_maladie',
            'Province_notification':'province_notification','Zone_de_sante_notification':'zone_de_sante_notification',
            'Aire_de_sante_notification':'aire_de_sante_notification','Semaine_epid':'semaine_epid','Num_semaine_epid':'num_semaine_epid',
            'Annee_epid':'annee_epid','Nom_complet':'nom_complet','Sexe':'sexe','Age_annee':'age_annee','Age_mois':'age_mois',
            'Age':'age','Unite_age':'unite_age','Age_en_ans':'age_en_ans','Tranche_age':'tranche_age','Tranche_age_en_ans':'tranche_age_en_ans',
            'Profession':'profession','Province_provenance':'province_provenance','Zone_de_sante_provenance':'zone_de_sante_provenance',
            'Aire_de_sante_provenance':'aire_de_sante_provenance','Adresse':'adresse','Symptomes':'symptomes',
            'Prise_antibiotique_avant_admission':'prise_antibiotique_avant_admission','Nom_antibiotique':'nom_antibiotique',
            'Antecedents_morbides':'antecedents_morbides','Femme_enceinte':'femme_enceinte','Degre_deshydratation':'degre_deshydratation',
            'Plan_de_deshydratation':'plan_de_deshydratation','Hospitalisation':'hospitalisation','Prelevement':'prelevement',
            'Date_prelevement':'date_prelevement','TDR_realise':'tdr_realise','TDR_Resultat':'tdr_resultat','TDR_archive':'tdr_archive',
            'Resultat_labo':'resultat_labo','Resultat_labo_culture':'resultat_labo_culture','Serotype':'serotype',
            'Nom_structure_realisant_le_tdr':'nom_structure_realisant_le_tdr','Resultat_labo_pcr':'resultat_labo_pcr',
            'Traitement_antibiotique':'traitement_antibiotique','Quantite_total_ringer_recue':'quantite_total_ringer_recue',
            'Quantite_total_sro_recue':'quantite_total_sro_recue','Ctc_utc':'ctc_utc','Issue':'issue','Date_sortie_au_CT':'date_sortie_au_ct',
            'Etat_sortie_malade':'etat_sortie_malade','Statut_vaccinal':'statut_vaccinal','Nombre_dose':'nombre_dose','Annee_vaccination':'annee_vaccination',
            'Source_eventuelle_de_contamination':'source_eventuelle_de_contamination','Source_approvisionnement_en_eau':'source_approvisionnement_en_eau',
            'Classification_finale':'classification_finale','Date_de_guerie':'date_de_guerie','Observation':'observation',
            'est_cas_suspect':'est_cas_suspect','est_cas_confirme':'est_cas_confirme','classification_auto':'classification_auto'
        }
        df = df.rename(columns=rename_map)

        # Convert dates
        for d in ['date_arrivee_malade','date_admission_au_ct','date_notification','date_investigation','date_debut_maladie','date_prelevement','date_sortie_au_ct','date_de_guerie']:
            if d in df.columns:
                df[d] = pd.to_datetime(df[d], errors='coerce')

        # Normalize boolean columns
        for b in ['est_cas_suspect','est_cas_confirme']:
            if b in df.columns:
                df[b] = df[b].astype('boolean')

        # Numeric conversions
        for n in ['num_semaine_epid','annee_epid','nombre_dose','Quantite_total_ringer_recue','Quantite_total_sro_recue']:
            if n in df.columns:
                df[n] = pd.to_numeric(df[n], errors='coerce')

        # Select columns present in DB
        db_cols = [
            'n_epid_prov','n_epid','statut_a_l_arrivee','date_arrivee_malade','date_admission_au_ct',
            'date_notification','date_investigation','date_debut_maladie','province_notification','zone_de_sante_notification',
            'aire_de_sante_notification','semaine_epid','num_semaine_epid','annee_epid','nom_complet','sexe','age_annee','age_mois','age',
            'unite_age','age_en_ans','tranche_age','tranche_age_en_ans','profession','province_provenance','zone_de_sante_provenance',
            'aire_de_sante_provenance','adresse','symptomes','prise_antibiotique_avant_admission','nom_antibiotique','antecedents_morbides',
            'femme_enceinte','degre_deshydratation','plan_de_deshydratation','hospitalisation','prelevement','date_prelevement','tdr_realise',
            'tdr_resultat','tdr_archive','resultat_labo','resultat_labo_culture','serotype','nom_structure_realisant_le_tdr','resultat_labo_pcr',
            'traitement_antibiotique','quantite_total_ringer_recue','quantite_total_sro_recue','ctc_utc','issue','date_sortie_au_ct','etat_sortie_malade',
            'statut_vaccinal','nombre_dose','annee_vaccination','source_eventuelle_de_contamination','source_approvisionnement_en_eau','classification_finale',
            'date_de_guerie','observation','est_cas_suspect','est_cas_confirme','classification_auto'
        ]
        df = df[[c for c in db_cols if c in df.columns]]

        with engine.begin() as conn:
            conn.execute(text('CREATE SCHEMA IF NOT EXISTS cholera'))
            df.to_sql('cas_ll', conn, schema='cholera', if_exists='append', index=False, method='multi')
        loaded += len(df)
        print('Loaded', len(df), 'rows from', path.name)

    print('Total LL rows loaded:', loaded)


def main():
    engine = get_engine()
    load_ids(engine)
    load_ll(engine)


if __name__ == '__main__':
    main()

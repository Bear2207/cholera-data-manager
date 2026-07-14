#!/usr/bin/env python3
"""Loader moderne pour charger les fichiers Excel dans la base Postgres.

Usage:
  pip install -r requirements.txt
  python scripts/load_data.py

Configuration via variables d'environnement (optionnel):
  POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT

Le script charge :
  - db/ids.xlsx (feuille 'db') -> schema cholera.cas_maladie
  - db/rdc_compilation*_LL_Cholera_*.xlsx (feuille 'LL_Cholera') -> cholera.cas_ll
"""
from pathlib import Path
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / 'db'
DEFAULT_PAYS = 'RDC'


def get_engine():
    user = os.environ.get('POSTGRES_USER', 'bearing')
    password = os.environ.get('POSTGRES_PASSWORD', 'Couspdata')
    db = os.environ.get('POSTGRES_DB', 'ids_db')
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
    return create_engine(url)


def ensure_schema(engine):
    schema_file = DB_DIR / 'init.sql'
    if not schema_file.exists():
        raise FileNotFoundError(f'Missing DB init file: {schema_file}')
    sql = schema_file.read_text(encoding='utf-8')
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def load_ids(engine):
    logger = logging.getLogger(__name__)
    path = DB_DIR / 'ids.xlsx'
    if not path.exists():
        logger.warning('IDS file not found: %s', path)
        return
    logger.info('Loading %s', path)
    df = pd.read_excel(path, sheet_name='db', engine='openpyxl')

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

    if 'debut_semaine_originale' in df.columns and 'debut_semaine' not in df.columns:
        df['debut_semaine'] = pd.to_datetime(df['debut_semaine_originale'], errors='coerce')

    int_cols = ['population', 'num_semaine', 'cas_tnn', 'deces_tnn', 'cas_0_11_mois', 'deces_0_11_mois',
                'cas_12_59_mois', 'deces_12_59_mois', 'cas_5_15_ans', 'deces_5_15_ans', 'cas_15_plus',
                'deces_15_plus', 'cas_total', 'deces_total', 'rec_status', 'unique_key']
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('Int64')

    df = df.where(pd.notnull(df), None)
    cols = [
        'code_zone', 'pays', 'province', 'zone_sante', 'population', 'num_semaine', 'annee',
        'debut_semaine_originale', 'debut_semaine', 'maladie', 'cas_tnn', 'deces_tnn',
        'cas_0_11_mois', 'deces_0_11_mois', 'cas_12_59_mois', 'deces_12_59_mois',
        'cas_5_15_ans', 'deces_5_15_ans', 'cas_15_plus', 'deces_15_plus', 'cas_total',
        'deces_total', 'letalite', 'taux_attaque', 'rec_status', 'unique_key'
    ]
    df = df[[c for c in cols if c in df.columns]]

    ensure_schema(engine)
    with engine.begin() as conn:
        df.to_sql('cas_maladie', conn, schema='cholera', if_exists='append', index=False, method='multi')
    logger.info('Loaded IDS rows: %d', len(df))
    sync_cas_maladie_lookup_ids(engine)


def load_ll(engine):
    logger = logging.getLogger(__name__)
    files = list(DB_DIR.glob('rdc_compilation*_LL_Cholera_*.xlsx'))
    if not files:
        possible = DB_DIR / 'rdc_compilation_LL_Cholera_SE01_SE52_04_01_2026_03_33_36.xlsx'
        files = [possible] if possible.exists() else []

    if not files:
        logger.warning('No LL files found in %s', DB_DIR)
        return

    loaded = 0
    ensure_schema(engine)
    for path in files:
        if not path.exists():
            continue
        logger.info('Loading LL file %s', path)
        xl = pd.ExcelFile(path, engine='openpyxl')
        if 'LL_Cholera' not in xl.sheet_names:
            logger.warning('No LL_Cholera sheet in %s', path)
            continue

        df = pd.read_excel(path, sheet_name='LL_Cholera', engine='openpyxl')
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
            'Statut_vaccinal': 'statut_vaccinal', 'Nombre_dose': 'nombre_dose', 'Annee_vaccination': 'annee_vaccination',
            'Source_eventuelle_de_contamination': 'source_eventuelle_de_contamination',
            'Source_approvisionnement_en_eau': 'source_approvisionnement_en_eau',
            'Classification_finale': 'classification_finale', 'Date_de_guerie': 'date_de_guerie',
            'Observation': 'observation', 'est_cas_suspect': 'est_cas_suspect',
            'est_cas_confirme': 'est_cas_confirme', 'classification_auto': 'classification_auto'
        }
        df = df.rename(columns=rename_map)

        date_cols = [
            'date_arrivee_malade', 'date_admission_au_ct', 'date_notification', 'date_investigation',
            'date_debut_maladie', 'date_prelevement', 'date_sortie_au_ct', 'date_de_guerie'
        ]
        for d in date_cols:
            if d in df.columns:
                df[d] = pd.to_datetime(df[d], errors='coerce')

        bool_cols = ['est_cas_suspect', 'est_cas_confirme']
        for b in bool_cols:
            if b in df.columns:
                df[b] = df[b].astype('boolean')

        numeric_cols = ['num_semaine_epid', 'annee_epid', 'nombre_dose', 'quantite_total_ringer_recue',
                        'quantite_total_sro_recue']
        for n in numeric_cols:
            if n in df.columns:
                df[n] = pd.to_numeric(df[n], errors='coerce')

        for c in df.select_dtypes(include=['object']).columns:
            df[c] = df[c].astype(str).str.strip().replace({'': None})

        df = df.where(pd.notnull(df), None)
        db_cols = [
            'n_epid_prov', 'n_epid', 'statut_a_l_arrivee', 'date_arrivee_malade', 'date_admission_au_ct',
            'date_notification', 'date_investigation', 'date_debut_maladie', 'province_notification',
            'zone_de_sante_notification', 'aire_de_sante_notification', 'semaine_epid', 'num_semaine_epid',
            'annee_epid', 'nom_complet', 'sexe', 'age_annee', 'age_mois', 'age', 'unite_age', 'age_en_ans',
            'tranche_age', 'tranche_age_en_ans', 'profession', 'province_provenance', 'zone_de_sante_provenance',
            'aire_de_sante_provenance', 'adresse', 'symptomes', 'prise_antibiotique_avant_admission',
            'nom_antibiotique', 'antecedents_morbides', 'femme_enceinte', 'degre_deshydratation',
            'plan_de_deshydratation', 'hospitalisation', 'prelevement', 'date_prelevement', 'tdr_realise',
            'tdr_resultat', 'tdr_archive', 'resultat_labo', 'resultat_labo_culture', 'serotype',
            'nom_structure_realisant_le_tdr', 'resultat_labo_pcr', 'traitement_antibiotique',
            'quantite_total_ringer_recue', 'quantite_total_sro_recue', 'ctc_utc', 'issue',
            'date_sortie_au_ct', 'etat_sortie_malade', 'statut_vaccinal', 'nombre_dose',
            'annee_vaccination', 'source_eventuelle_de_contamination',
            'source_approvisionnement_en_eau', 'classification_finale', 'date_de_guerie', 'observation',
            'est_cas_suspect', 'est_cas_confirme', 'classification_auto'
        ]
        df = df[[c for c in db_cols if c in df.columns]]

        with engine.begin() as conn:
            df.to_sql('cas_ll', conn, schema='cholera', if_exists='append', index=False, method='multi')
        loaded += len(df)
        logger.info('Loaded %d rows from %s', len(df), path.name)

    if loaded:
        sync_cas_ll_lookup_ids(engine)
    logger.info('Total LL rows loaded: %d', loaded)


def sync_cas_maladie_lookup_ids(engine):
    logger = logging.getLogger(__name__)
    with engine.begin() as conn:
        logger.info('Syncing cas_maladie lookup tables')
        conn.execute(text("""
INSERT INTO cholera.pays (nom)
SELECT DISTINCT NULLIF(trim(both from pays), '')
FROM cholera.cas_maladie
WHERE pays IS NOT NULL AND trim(both from pays) <> ''
ON CONFLICT (nom) DO NOTHING
"""))

        conn.execute(text("""
INSERT INTO cholera.province (pays_id, nom)
SELECT DISTINCT p.id, NULLIF(trim(both from province), '')
FROM cholera.cas_maladie cm
JOIN cholera.pays p ON trim(lower(cm.pays)) = trim(lower(p.nom))
WHERE cm.province IS NOT NULL AND trim(both from cm.province) <> ''
ON CONFLICT (pays_id, nom) DO NOTHING
"""))

        conn.execute(text("""
INSERT INTO cholera.zone_sante (province_id, nom)
SELECT DISTINCT pr.id, NULLIF(trim(both from zone_sante), '')
FROM cholera.cas_maladie cm
JOIN cholera.province pr ON trim(lower(cm.province)) = trim(lower(pr.nom))
JOIN cholera.pays p ON pr.pays_id = p.id AND trim(lower(cm.pays)) = trim(lower(p.nom))
WHERE cm.zone_sante IS NOT NULL AND trim(both from cm.zone_sante) <> ''
ON CONFLICT (province_id, nom) DO NOTHING
"""))

        conn.execute(text("""
INSERT INTO cholera.maladie (nom)
SELECT DISTINCT NULLIF(trim(both from maladie), '')
FROM cholera.cas_maladie
WHERE maladie IS NOT NULL AND trim(both from maladie) <> ''
ON CONFLICT (nom) DO NOTHING
"""))

        conn.execute(text("""
UPDATE cholera.cas_maladie cm
SET pays_id = p.id
FROM cholera.pays p
WHERE cm.pays IS NOT NULL AND trim(lower(cm.pays)) = trim(lower(p.nom))
"""))

        conn.execute(text("""
UPDATE cholera.cas_maladie cm
SET province_id = pr.id
FROM cholera.province pr
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cm.province IS NOT NULL
  AND trim(lower(cm.province)) = trim(lower(pr.nom))
  AND trim(lower(cm.pays)) = trim(lower(p.nom))
"""))

        conn.execute(text("""
UPDATE cholera.cas_maladie cm
SET zone_sante_id = z.id
FROM cholera.zone_sante z
JOIN cholera.province pr ON z.province_id = pr.id
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cm.zone_sante IS NOT NULL
  AND trim(lower(cm.zone_sante)) = trim(lower(z.nom))
  AND trim(lower(cm.province)) = trim(lower(pr.nom))
  AND trim(lower(cm.pays)) = trim(lower(p.nom))
"""))

        conn.execute(text("""
UPDATE cholera.cas_maladie cm
SET maladie_id = m.id
FROM cholera.maladie m
WHERE cm.maladie IS NOT NULL AND trim(lower(cm.maladie)) = trim(lower(m.nom))
"""))

        logger.info('cas_maladie lookup sync complete')


def sync_cas_ll_lookup_ids(engine):
    logger = logging.getLogger(__name__)
    with engine.begin() as conn:
        logger.info('Syncing cas_ll lookup tables')
        conn.execute(text("""
INSERT INTO cholera.pays (nom)
VALUES (:pays)
ON CONFLICT (nom) DO NOTHING
"""), {'pays': DEFAULT_PAYS})

        conn.execute(text("""
INSERT INTO cholera.province (pays_id, nom)
SELECT DISTINCT p.id, name
FROM (
    SELECT NULLIF(trim(both from province_notification), '') AS name FROM cholera.cas_ll
    UNION
    SELECT NULLIF(trim(both from province_provenance), '') AS name FROM cholera.cas_ll
) sub
JOIN cholera.pays p ON trim(lower(p.nom)) = trim(lower(:pays))
WHERE name IS NOT NULL
ON CONFLICT (pays_id, nom) DO NOTHING
"""), {'pays': DEFAULT_PAYS})

        conn.execute(text("""
WITH zone_names AS (
    SELECT DISTINCT NULLIF(trim(both from zone_de_sante_notification), '') AS nom,
           NULLIF(trim(both from province_notification), '') AS province_name
    FROM cholera.cas_ll
    UNION
    SELECT DISTINCT NULLIF(trim(both from zone_de_sante_provenance), '') AS nom,
           NULLIF(trim(both from province_provenance), '') AS province_name
    FROM cholera.cas_ll
)
INSERT INTO cholera.zone_sante (province_id, nom)
SELECT DISTINCT pr.id, zn.nom
FROM zone_names zn
JOIN cholera.province pr ON trim(lower(pr.nom)) = trim(lower(zn.province_name))
JOIN cholera.pays p ON pr.pays_id = p.id AND trim(lower(p.nom)) = trim(lower(:pays))
WHERE zn.nom IS NOT NULL AND zn.province_name IS NOT NULL
ON CONFLICT (province_id, nom) DO NOTHING
"""), {'pays': DEFAULT_PAYS})

        lookups = [
            ('sexe', 'sexe'), ('unite_age', 'unite_age'), ('hospitalisation', 'hospitalisation_status'),
            ('prelevement', 'prelevement_status'), ('tdr_realise', 'tdr_realise_status'),
            ('tdr_resultat', 'tdr_resultat_status'), ('resultat_labo', 'resultat_labo_status'),
            ('resultat_labo_culture', 'resultat_labo_culture_status'), ('resultat_labo_pcr', 'resultat_labo_pcr_status'),
            ('issue', 'issue'), ('statut_vaccinal', 'statut_vaccinal_status'),
            ('classification_finale', 'classification_finale')
        ]
        for source_col, lookup_table in lookups:
            conn.execute(text(f"""
INSERT INTO cholera.{lookup_table} (nom)
SELECT DISTINCT NULLIF(trim(both from {source_col}), '')
FROM cholera.cas_ll
WHERE {source_col} IS NOT NULL AND trim(both from {source_col}) <> ''
ON CONFLICT (nom) DO NOTHING
"""))

        conn.execute(text("""
UPDATE cholera.cas_ll cl
SET province_notification_id = pr.id
FROM cholera.province pr
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cl.province_notification IS NOT NULL
  AND trim(lower(cl.province_notification)) = trim(lower(pr.nom))
  AND trim(lower(p.nom)) = trim(lower(:pays))
"""), {'pays': DEFAULT_PAYS})

        conn.execute(text("""
UPDATE cholera.cas_ll cl
SET province_provenance_id = pr.id
FROM cholera.province pr
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cl.province_provenance IS NOT NULL
  AND trim(lower(cl.province_provenance)) = trim(lower(pr.nom))
  AND trim(lower(p.nom)) = trim(lower(:pays))
"""), {'pays': DEFAULT_PAYS})

        conn.execute(text("""
UPDATE cholera.cas_ll cl
SET zone_de_sante_notification_id = z.id
FROM cholera.zone_sante z
JOIN cholera.province pr ON z.province_id = pr.id
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cl.zone_de_sante_notification IS NOT NULL
  AND trim(lower(cl.zone_de_sante_notification)) = trim(lower(z.nom))
  AND cl.province_notification IS NOT NULL
  AND trim(lower(cl.province_notification)) = trim(lower(pr.nom))
  AND trim(lower(p.nom)) = trim(lower(:pays))
"""), {'pays': DEFAULT_PAYS})

        conn.execute(text("""
UPDATE cholera.cas_ll cl
SET zone_de_sante_provenance_id = z.id
FROM cholera.zone_sante z
JOIN cholera.province pr ON z.province_id = pr.id
JOIN cholera.pays p ON pr.pays_id = p.id
WHERE cl.zone_de_sante_provenance IS NOT NULL
  AND trim(lower(cl.zone_de_sante_provenance)) = trim(lower(z.nom))
  AND cl.province_provenance IS NOT NULL
  AND trim(lower(cl.province_provenance)) = trim(lower(pr.nom))
  AND trim(lower(p.nom)) = trim(lower(:pays))
"""), {'pays': DEFAULT_PAYS})

        for source_col, lookup_table in lookups:
            dest_col = f'{source_col}_id'
            if source_col == 'classification_finale':
                dest_col = 'classification_finale_id'
            elif source_col == 'statut_vaccinal':
                dest_col = 'statut_vaccinal_id'
            elif source_col == 'hospitalisation':
                dest_col = 'hospitalisation_id'
            elif source_col == 'prelevement':
                dest_col = 'prelevement_id'
            elif source_col == 'unite_age':
                dest_col = 'unite_age_id'
            elif source_col == 'tdr_realise':
                dest_col = 'tdr_realise_id'
            elif source_col == 'tdr_resultat':
                dest_col = 'tdr_resultat_id'
            elif source_col == 'resultat_labo':
                dest_col = 'resultat_labo_id'
            elif source_col == 'resultat_labo_culture':
                dest_col = 'resultat_labo_culture_id'
            elif source_col == 'resultat_labo_pcr':
                dest_col = 'resultat_labo_pcr_id'
            elif source_col == 'issue':
                dest_col = 'issue_id'
            elif source_col == 'sexe':
                dest_col = 'sexe_id'
            conn.execute(text(f"""
UPDATE cholera.cas_ll cl
SET {dest_col} = lt.id
FROM cholera.{lookup_table} lt
WHERE cl.{source_col} IS NOT NULL
  AND trim(lower(cl.{source_col})) = trim(lower(lt.nom))
"""))

        logger.info('cas_ll lookup sync complete')


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    engine = get_engine()
    load_ids(engine)
    load_ll(engine)


if __name__ == '__main__':
    main()

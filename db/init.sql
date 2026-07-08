-- Activer PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Schéma dédié à l'application cholera-data-manager
CREATE SCHEMA IF NOT EXISTS cholera;
SET search_path TO cholera, public;

-- Domaines réutilisables et validations simples
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'positive_integer') THEN
        CREATE DOMAIN positive_integer AS INTEGER
            CHECK (VALUE >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'week_number') THEN
        CREATE DOMAIN week_number AS SMALLINT
            CHECK (VALUE BETWEEN 1 AND 53);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'percentage') THEN
        CREATE DOMAIN percentage AS NUMERIC(5,2)
            CHECK (VALUE >= 0 AND VALUE <= 100);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'non_empty_text') THEN
        CREATE DOMAIN non_empty_text AS TEXT
            CHECK (char_length(trim(BOTH FROM VALUE)) > 0);
    END IF;
END$$;

-- Trigger helper for updated_at
CREATE OR REPLACE FUNCTION cholera.refresh_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tables de référence pour une structure plus relationnelle
CREATE TABLE IF NOT EXISTS cholera.pays (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.province (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pays_id INTEGER NOT NULL REFERENCES cholera.pays(id),
    nom VARCHAR(100) NOT NULL,
    UNIQUE (pays_id, nom)
);

CREATE TABLE IF NOT EXISTS cholera.zone_sante (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    province_id INTEGER NOT NULL REFERENCES cholera.province(id),
    nom VARCHAR(100) NOT NULL,
    UNIQUE (province_id, nom)
);

CREATE TABLE IF NOT EXISTS cholera.maladie (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.issue (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.sexe (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.unite_age (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.prelevement_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.tdr_realise_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.tdr_resultat_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.resultat_labo_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.resultat_labo_culture_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.resultat_labo_pcr_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.hospitalisation_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.statut_vaccinal_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cholera.classification_finale (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

-- Table principale pour les données IDS
CREATE TABLE IF NOT EXISTS cholera.cas_maladie (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code_zone VARCHAR(50) NOT NULL,
    pays VARCHAR(50) NOT NULL DEFAULT 'RDC',
    province VARCHAR(50) NOT NULL,
    zone_sante VARCHAR(100) NOT NULL,
    pays_id INTEGER REFERENCES cholera.pays(id),
    province_id INTEGER REFERENCES cholera.province(id),
    zone_sante_id INTEGER REFERENCES cholera.zone_sante(id),
    population positive_integer NOT NULL DEFAULT 0,
    num_semaine week_number NOT NULL,
    annee INTEGER NOT NULL,
    debut_semaine_originale DATE,
    debut_semaine DATE NOT NULL,
    maladie VARCHAR(50) NOT NULL,
    maladie_id INTEGER REFERENCES cholera.maladie(id),
    cas_tnn positive_integer NOT NULL DEFAULT 0,
    deces_tnn positive_integer NOT NULL DEFAULT 0,
    cas_0_11_mois positive_integer NOT NULL DEFAULT 0,
    deces_0_11_mois positive_integer NOT NULL DEFAULT 0,
    cas_12_59_mois positive_integer NOT NULL DEFAULT 0,
    deces_12_59_mois positive_integer NOT NULL DEFAULT 0,
    cas_5_15_ans positive_integer NOT NULL DEFAULT 0,
    deces_5_15_ans positive_integer NOT NULL DEFAULT 0,
    cas_15_plus positive_integer NOT NULL DEFAULT 0,
    deces_15_plus positive_integer NOT NULL DEFAULT 0,
    cas_total positive_integer GENERATED ALWAYS AS (
        cas_tnn + cas_0_11_mois + cas_12_59_mois + cas_5_15_ans + cas_15_plus
    ) STORED,
    deces_total positive_integer GENERATED ALWAYS AS (
        deces_tnn + deces_0_11_mois + deces_12_59_mois + deces_5_15_ans + deces_15_plus
    ) STORED,
    letalite percentage GENERATED ALWAYS AS (
        CASE WHEN cas_total > 0 THEN (deces_total::NUMERIC / cas_total) * 100 ELSE NULL END
    ) STORED,
    taux_attaque NUMERIC(10,4) CHECK (taux_attaque >= 0),
    rec_status INTEGER,
    unique_key INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT unique_case UNIQUE (code_zone, num_semaine, maladie_id)
);

CREATE INDEX IF NOT EXISTS idx_cas_maladie_code_zone ON cholera.cas_maladie(code_zone);
CREATE INDEX IF NOT EXISTS idx_cas_maladie_province ON cholera.cas_maladie(province);
CREATE INDEX IF NOT EXISTS idx_cas_maladie_debut_semaine ON cholera.cas_maladie(debut_semaine);

CREATE TRIGGER cas_maladie_updated_at
    BEFORE UPDATE ON cholera.cas_maladie
    FOR EACH ROW EXECUTE FUNCTION cholera.refresh_updated_at();

-- Table pour les données LL Cholera (adaptée à l'Excel)
CREATE TABLE IF NOT EXISTS cholera.cas_ll (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Identifiants
    n_epid_prov VARCHAR(50) NOT NULL,
    n_epid VARCHAR(50) NOT NULL,
    statut_a_l_arrivee VARCHAR(20),
    date_arrivee_malade DATE,
    date_admission_au_ct DATE,
    date_notification DATE,
    date_investigation DATE,
    date_debut_maladie DATE,

    -- Géographie
    province_notification VARCHAR(50) NOT NULL,
    zone_de_sante_notification VARCHAR(100) NOT NULL,
    province_notification_id INTEGER REFERENCES cholera.province(id),
    zone_de_sante_notification_id INTEGER REFERENCES cholera.zone_sante(id),
    aire_de_sante_notification VARCHAR(100),

    -- Période
    semaine_epid VARCHAR(20),
    num_semaine_epid week_number,
    annee_epid INTEGER,

    -- Patient
    nom_complet VARCHAR(100),
    sexe VARCHAR(10),
    sexe_id INTEGER REFERENCES cholera.sexe(id),
    age_annee NUMERIC(6,2),
    age_mois NUMERIC(6,2),
    age NUMERIC(6,2),
    unite_age VARCHAR(20),
    unite_age_id INTEGER REFERENCES cholera.unite_age(id),
    age_en_ans NUMERIC(6,2),
    tranche_age VARCHAR(20),
    tranche_age_en_ans VARCHAR(20),
    profession VARCHAR(100),

    -- Provenance
    province_provenance VARCHAR(50),
    zone_de_sante_provenance VARCHAR(100),
    province_provenance_id INTEGER REFERENCES cholera.province(id),
    zone_de_sante_provenance_id INTEGER REFERENCES cholera.zone_sante(id),
    aire_de_sante_provenance VARCHAR(100),
    adresse TEXT,

    -- Clinique
    symptomes TEXT,
    prise_antibiotique_avant_admission VARCHAR(5),
    nom_antibiotique VARCHAR(50),
    antecedents_morbides VARCHAR(50),
    femme_enceinte VARCHAR(5),
    degre_deshydratation VARCHAR(20),
    plan_de_deshydratation VARCHAR(20),
    hospitalisation VARCHAR(5),
    hospitalisation_id INTEGER REFERENCES cholera.hospitalisation_status(id),

    -- Examens
    prelevement VARCHAR(5),
    prelevement_id INTEGER REFERENCES cholera.prelevement_status(id),
    date_prelevement DATE,
    tdr_realise VARCHAR(5),
    tdr_realise_id INTEGER REFERENCES cholera.tdr_realise_status(id),
    tdr_resultat VARCHAR(20),
    tdr_resultat_id INTEGER REFERENCES cholera.tdr_resultat_status(id),
    tdr_archive VARCHAR(20),
    resultat_labo VARCHAR(20),
    resultat_labo_id INTEGER REFERENCES cholera.resultat_labo_status(id),
    resultat_labo_culture VARCHAR(20),
    resultat_labo_culture_id INTEGER REFERENCES cholera.resultat_labo_culture_status(id),
    serotype VARCHAR(20),
    nom_structure_realisant_le_tdr VARCHAR(100),
    resultat_labo_pcr VARCHAR(20),
    resultat_labo_pcr_id INTEGER REFERENCES cholera.resultat_labo_pcr_status(id),

    -- Traitement
    traitement_antibiotique VARCHAR(20),
    quantite_total_ringer_recue NUMERIC(10,2),
    quantite_total_sro_recue NUMERIC(10,2),
    ctc_utc VARCHAR(50),

    -- Issue
    issue VARCHAR(20),
    issue_id INTEGER REFERENCES cholera.issue(id),
    date_sortie_au_ct DATE,
    etat_sortie_malade VARCHAR(20),
    statut_vaccinal VARCHAR(10),
    statut_vaccinal_id INTEGER REFERENCES cholera.statut_vaccinal_status(id),
    nombre_dose INTEGER,
    annee_vaccination INTEGER,
    source_eventuelle_de_contamination TEXT,
    source_approvisionnement_en_eau TEXT,
    classification_finale VARCHAR(50),
    classification_finale_id INTEGER REFERENCES cholera.classification_finale(id),
    est_cas_suspect BOOLEAN,
    est_cas_confirme BOOLEAN,
    classification_auto VARCHAR(50),
    date_de_guerie DATE,
    observation TEXT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    UNIQUE (n_epid, province_notification, num_semaine_epid, annee_epid)
);

CREATE INDEX IF NOT EXISTS idx_cas_ll_n_epid ON cholera.cas_ll(n_epid);
CREATE INDEX IF NOT EXISTS idx_cas_ll_province_notification ON cholera.cas_ll(province_notification);
CREATE INDEX IF NOT EXISTS idx_cas_ll_date_debut_maladie ON cholera.cas_ll(date_debut_maladie);

CREATE TRIGGER cas_ll_updated_at
    BEFORE UPDATE ON cholera.cas_ll
    FOR EACH ROW EXECUTE FUNCTION cholera.refresh_updated_at();

-- Table des zones
CREATE TABLE IF NOT EXISTS cholera.zones (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    province VARCHAR(50) NOT NULL,
    population positive_integer NOT NULL DEFAULT 0,
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_zones_geom ON cholera.zones USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_zones_province ON cholera.zones(province);

CREATE TRIGGER zones_updated_at
    BEFORE UPDATE ON cholera.zones
    FOR EACH ROW EXECUTE FUNCTION cholera.refresh_updated_at();

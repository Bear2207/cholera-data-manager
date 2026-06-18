-- Activer PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table principale pour les données IDS (inchangée)
CREATE TABLE IF NOT EXISTS cas_maladie (
    id SERIAL PRIMARY KEY,
    code_zone VARCHAR(50),
    pays VARCHAR(50),
    province VARCHAR(50),
    zone_sante VARCHAR(100),
    population INTEGER,
    num_semaine INTEGER,
    debut_semaine DATE,
    maladie VARCHAR(50),
    cas_tnn INTEGER,
    deces_tnn INTEGER,
    cas_0_11_mois INTEGER,
    deces_0_11_mois INTEGER,
    cas_12_59_mois INTEGER,
    deces_12_59_mois INTEGER,
    cas_5_15_ans INTEGER,
    deces_5_15_ans INTEGER,
    cas_15_plus INTEGER,
    deces_15_plus INTEGER,
    cas_total INTEGER,
    deces_total INTEGER,
    letalite FLOAT,
    taux_attaque FLOAT,
    rec_status INTEGER,
    unique_key INTEGER
);
ALTER TABLE cas_maladie ADD CONSTRAINT unique_case UNIQUE (code_zone, num_semaine, maladie);

-- Table pour les données LL Cholera (adaptée à l'Excel)
CREATE TABLE IF NOT EXISTS cas_ll (
    id SERIAL PRIMARY KEY,
    
    -- Identifiants
    n_epid_prov VARCHAR(50),
    n_epid VARCHAR(50),
    statut_a_l_arrivee VARCHAR(20),
    date_arrivee_malade DATE,
    date_admission_au_ct DATE,
    date_notification DATE,
    date_investigation DATE,
    date_debut_maladie DATE,
    
    -- Géographie
    province_notification VARCHAR(50),
    zone_de_sante_notification VARCHAR(100),
    aire_de_sante_notification VARCHAR(100),
    
    -- Période
    semaine_epid VARCHAR(20),
    num_semaine_epid INTEGER,
    annee_epid INTEGER,
    
    -- Patient
    nom_complet VARCHAR(100),
    sexe VARCHAR(10),
    age_annee FLOAT,          -- peut être NULL ou contenir des ".0"
    age_mois FLOAT,
    age FLOAT,                -- colonne "Age" (peut être vide ou numérique)
    unite_age VARCHAR(20),
    age_en_ans FLOAT,
    tranche_age VARCHAR(20),
    tranche_age_en_ans VARCHAR(20),
    profession VARCHAR(100),
    
    -- Provenance
    province_provenance VARCHAR(50),
    zone_de_sante_provenance VARCHAR(100),
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
    
    -- Examens
    prelevement VARCHAR(5),
    date_prelevement DATE,
    tdr_realise VARCHAR(5),
    tdr_resultat VARCHAR(20),
    tdr_archive VARCHAR(20),
    resultat_labo VARCHAR(20),
    resultat_labo_culture VARCHAR(20),
    serotype VARCHAR(20),
    nom_structure_realisant_le_tdr VARCHAR(100),
    resultat_labo_pcr VARCHAR(20),
    
    -- Traitement
    traitement_antibiotique VARCHAR(20),
    quantite_total_ringer_recue FLOAT,
    quantite_total_sro_recue FLOAT,
    ctc_utc VARCHAR(50),
    
    -- Issue
    issue VARCHAR(20),
    date_sortie_au_ct DATE,
    etat_sortie_malade VARCHAR(20),
    statut_vaccinal VARCHAR(10),
    nombre_dose INTEGER,
    annee_vaccination FLOAT,
    source_eventuelle_de_contamination TEXT,
    source_approvisionnement_en_eau TEXT,
    classification_finale VARCHAR(50),
    date_de_guerie DATE,
    observation TEXT,
    
    -- Contrainte d'unicité (pour éviter les doublons)
    UNIQUE (n_epid, province_notification, num_semaine_epid, annee_epid)
);

-- Table des zones (inchangée)
CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    province VARCHAR(50),
    population INTEGER,
    geom GEOMETRY(MULTIPOLYGON, 4326)
);
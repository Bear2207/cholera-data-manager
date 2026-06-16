-- Activer PostGIS (si vous l'utilisez pour les zones)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table principale pour les données épidémiologiques
CREATE TABLE IF NOT EXISTS cas_maladie (
    id SERIAL PRIMARY KEY,

    -- Identifiants et géographie
    code_zone VARCHAR(50),          -- correspond à la colonne NUM
    pays VARCHAR(50),
    province VARCHAR(50),
    zone_sante VARCHAR(100),
    population INTEGER,

    -- Période
    num_semaine INTEGER,
    debut_semaine DATE,

    -- Maladie
    maladie VARCHAR(50),

    -- Cas et décès par tranche d'âge
    -- TNN (probablement < 1 an ou nouveau-né)
    cas_tnn INTEGER,
    deces_tnn INTEGER,

    -- 0-11 mois
    cas_0_11_mois INTEGER,
    deces_0_11_mois INTEGER,

    -- 12-59 mois
    cas_12_59_mois INTEGER,
    deces_12_59_mois INTEGER,

    -- 5-15 ans
    cas_5_15_ans INTEGER,
    deces_5_15_ans INTEGER,

    -- 15 ans et plus
    cas_15_plus INTEGER,
    deces_15_plus INTEGER,

    -- Totaux
    cas_total INTEGER,
    deces_total INTEGER,

    -- Indicateurs (en pourcentage, stockés en float)
    letalite FLOAT,      -- valeur en % (ex: 2.5 pour 2,5%)
    taux_attaque FLOAT,  -- valeur pour 1000 ou 100000 habitants (selon votre source)

    -- Métadonnées
    rec_status INTEGER,   -- 0/1 ou NULL
    unique_key INTEGER    -- clé unique (si utile)
);

-- Table des zones avec géométries (si vous souhaitez stocker les limites)
CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    province VARCHAR(50),
    population INTEGER,
    geom GEOMETRY(MULTIPOLYGON, 4326)
);
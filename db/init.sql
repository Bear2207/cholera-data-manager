-- Activer PostGIS

CREATE EXTENSION IF NOT EXISTS postgis;

-- Table principale pour les données choléra

CREATE TABLE IF NOT EXISTS cas_maladie (id SERIAL PRIMARY KEY,
                                                  pays VARCHAR(50),
                                                       province VARCHAR(50),
                                                                zone_sante VARCHAR(100),
                                                                           population INT, num_semaine INT, debut_semaine DATE, maladie VARCHAR(50),
                                                                                                                                        cas_total INT, deces_total INT, letalite FLOAT, taux_attaque FLOAT);

-- Table des zones avec géométries

CREATE TABLE IF NOT EXISTS zones (id SERIAL PRIMARY KEY,
                                            nom VARCHAR(100),
                                                province VARCHAR(50),
                                                         population INT, geom GEOMETRY(MULTIPOLYGON, 4326) -- Stockage des limites géographiques
);
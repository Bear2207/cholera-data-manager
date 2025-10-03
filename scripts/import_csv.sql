-- Script pour importer les données CSV dans la table cas_maladie
-- Assurez-vous que le fichier CSV est accessible depuis le conteneur PostgreSQL
-- et que le chemin est correct.
-- executé dans le conteneur postgres via psql -U bearing -d maladie_db -f /scripts/import_csv.sql

docker exec -it cousp_maladie_DB psql -U bearing -d maladie_db

\copy cas_maladie(pays, province, zone_sante, population, num_semaine, debut_semaine, maladie, cas_total, deces_total, letalite, taux_attaque)
FROM '/db/data/donnees_maladie.csv'
DELIMITER ',' CSV HEADER;

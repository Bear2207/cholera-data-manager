-- Script pour importer les données CSV dans la table cas_maladie
-- Assurez-vous que le fichier CSV est accessible depuis le conteneur PostgreSQL
-- et que le chemin est correct.
-- executé dans le conteneur postgres via psql -U bearing -d ids_db -f /scripts/import_csv.sql

docker exec -it cousp_db psql -U bearing -d ids_db -c "\COPY cas_maladie (
    code_zone, pays, province, zone_sante, population,
    num_semaine, debut_semaine, maladie,
    cas_tnn, deces_tnn,
    cas_0_11_mois, deces_0_11_mois,
    cas_12_59_mois, deces_12_59_mois,
    cas_5_15_ans, deces_5_15_ans,
    cas_15_plus, deces_15_plus,
    cas_total, deces_total,
    letalite, taux_attaque,
    rec_status, unique_key
)

FROM 'C:\Users\beari\Documents\cholera-data-manager\cholera-data-manager\db\data\donnees_maladie.csv'
DELIMITER ',' CSV HEADER NULL 'NULL';